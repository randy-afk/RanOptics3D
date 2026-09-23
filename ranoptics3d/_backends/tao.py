"""
ranoptics3d._backends.tao
=========================
Tao / Bmad backend — loads lattice via pytao.
"""
from __future__ import annotations
import os, re, tempfile
from pathlib import Path


def _is_shared_lib_name(fname):
    return '.so' in fname or fname.endswith('.dylib') or fname.endswith('.dll')


def _preload_staged_libs(staging_dir, skip_basename):
    """Explicitly dlopen() every staged library except skip_basename,
    before libtao.so itself gets loaded.

    Why: directory-based staging (see _stage_bmad_lib) isn't reliable on
    its own. If a frozen PyInstaller build happens to ALSO bundle a
    library with the same name in its own _MEIPASS (e.g. libssl.so.3,
    pulled in for Python's own ssl module or Qt's network stack), that
    copy can win over our staged one when some OTHER staged library goes
    looking for it by SONAME — even though the correct version is sitting
    right next to it in the staging directory. Confirmed in practice on
    RanOptics (2D, same pytao/Bmad dependency): a real user's build
    failed with "libssl.so.3: version OPENSSL_3.2.0 not found (required
    by .../libcurl.so.4)" — libcurl.so.4 needed a newer OpenSSL than the
    one PyInstaller had bundled for its own purposes, even though the
    correct one was staged alongside it.

    Explicitly loading our correct copies first, with RTLD_GLOBAL, means
    that by the time libtao.so (or any of its dependencies) looks for
    something like libssl.so.3, the dynamic linker finds it ALREADY
    resident in the process (matched by soname) and reuses it instead of
    searching the filesystem and risking a different, wrong copy.

    Order isn't known upfront, so this retries in passes: a library
    whose own dependencies haven't loaded yet will fail and gets retried
    once something else has succeeded. Stops once nothing more loads.
    """
    import ctypes
    remaining = {f for f in os.listdir(staging_dir) if f != skip_basename}
    for _ in range(len(remaining) + 1):
        if not remaining:
            break
        progressed = False
        for fname in list(remaining):
            try:
                ctypes.CDLL(os.path.join(staging_dir, fname), mode=ctypes.RTLD_GLOBAL)
                remaining.discard(fname)
                progressed = True
            except OSError:
                pass
        if not progressed:
            break


def _stage_bmad_lib(bmad_lib, extra_paths):
    """Stage symlinks (falling back to copies) to bmad_lib and every shared
    library in extra_paths into one fresh temp directory, preload them
    (see _preload_staged_libs), and return the path to the staged copy of
    bmad_lib.

    Why staging at all: dlopen()/ctypes.CDLL() resolves a shared
    library's own dependencies (DT_NEEDED entries) by searching the SAME
    DIRECTORY as the library itself — confirmed empirically, this is
    what actually makes a plain conda-forge install "just work" with no
    env vars at all, since GSL/LAPACK/etc. sit right next to libtao.so.
    Setting LD_LIBRARY_PATH from Python does NOT work: glibc's loader
    reads and caches that variable once at process start, before any
    Python code runs, and never re-reads it for later dlopen() calls. So
    when a user's dependencies are scattered across directories, the
    only mechanism that reaches them is putting everything in one
    directory ourselves before loading.
    """
    staging_dir = tempfile.mkdtemp(prefix='ranoptics3d_bmad_')
    bmad_lib = os.path.abspath(bmad_lib)
    for src_dir in [os.path.dirname(bmad_lib), *(os.path.abspath(p) for p in extra_paths)]:
        if not src_dir or not os.path.isdir(src_dir):
            continue
        for fname in os.listdir(src_dir):
            if not _is_shared_lib_name(fname):
                continue
            src = os.path.join(src_dir, fname)
            dst = os.path.join(staging_dir, fname)
            if os.path.exists(dst) or not os.path.isfile(src):
                continue
            try:
                os.symlink(src, dst)
            except OSError:
                try:
                    import shutil
                    shutil.copy2(src, dst)
                except OSError:
                    pass
    _preload_staged_libs(staging_dir, os.path.basename(bmad_lib))
    return os.path.join(staging_dir, os.path.basename(bmad_lib))


def _make_tao(cmd, bmad_lib=None, bmad_extra_paths=None):
    """Construct a pytao.Tao instance, optionally pointed at an explicit
    Bmad shared library.

    bmad_lib: optional explicit path to libtao.so/.dylib/.dll. Only needed
    in the standalone packaged build. pytao's own auto-discovery
    (ACC_ROOT_DIR / ctypes.util.find_library) works fine when running from
    source with Bmad on the environment, but a frozen PyInstaller
    executable has no RPATH into wherever Bmad is installed — so the
    library must be pointed at explicitly, bypassing auto-discovery
    entirely via pytao's own so_lib= parameter.

    bmad_extra_paths: optional list of additional directories to search
    for libtao's own dependencies (GSL, LAPACK, FFTW3, HDF5, etc), for
    cases where those aren't sitting next to bmad_lib itself.

    bmad_lib always gets staged (see _stage_bmad_lib()) when given, even
    with no extra paths — relying on "the dependencies happen to already
    be next to bmad_lib" turned out to depend on unrelated import order
    rather than being guaranteed. Staging unconditionally makes this
    deterministic.
    """
    if bmad_lib:
        bmad_lib = _stage_bmad_lib(bmad_lib, bmad_extra_paths or [])
    from pytao import Tao
    return Tao(cmd, so_lib=bmad_lib) if bmad_lib else Tao(cmd)


def _parse_tao_init(init_file):
    """Read n_universes and design_lattice file labels from a Tao .init file."""
    try:
        with open(init_file, 'r') as f:
            content = f.read()
    except Exception:
        return 1, {1: 'u1'}
    n = 1
    m = re.search(r'n_universes\s*=\s*(\d+)', content, re.IGNORECASE)
    if m:
        n = int(m.group(1))
    labels = {}
    pat = re.compile(
        r"design_lattice\s*\((\d+)\)\s*%\s*file\s*=\s*['\"]?([^\s'\"&,/]+)",
        re.IGNORECASE)
    for m2 in pat.finditer(content):
        idx = int(m2.group(1))
        path = m2.group(2).strip()
        stem = Path(path).stem
        label = stem.split('_')[0] if '_' in stem else stem
        labels[idx] = label
    for i in range(1, n + 1):
        labels.setdefault(i, f'u{i}')
    return n, labels


def _load_tao_universe(tao, uni_idx, log_fn=None):
    def L(m):
        (log_fn(m + '\n') if log_fn else print(m))

    u = f"-universe {uni_idx}"
    u_at = f"{uni_idx}@"
    result = tao.cmd(
        f"show lattice {u} -all -att K1 -att K2 -att hkick -att vkick -att ref_tilt")
    elems = []
    for line in result:
        if 'Lord Elements:' in line:
            break
        if line.startswith('#') or not line.strip():
            continue
        p = line.split()
        try:
            idx = int(p[0])
            name = p[1]
            key = p[2]
            s_end = float(p[3])
            length = float(p[4]) if p[4] != '---' else 0.0

            def _f(i):
                return float(p[i]) if len(p) > i and p[i] != '---' else 0.0

            kl = key.lower()
            hk = _f(6); vk = _f(7)
            kick = hk if kl == 'hkicker' else (vk if kl == 'vkicker' else 0.0)
            elems.append({
                'name': name, 'key': key, 'index': idx,
                's_start': s_end - length, 'length': length,
                'angle': 0.0, 'k1': _f(5), 'k2': _f(6) if kl != 'hkicker' else 0.0,
                'hkick': hk, 'vkick': vk, 'kick': kick,
                'ref_tilt': _f(8),
            })
        except (IndexError, ValueError):
            continue

    # Re-fetch K2 and ref_tilt with explicit attribute order
    result = tao.cmd(
        f"show lattice {u} -all -att K1 -att K2 -att ref_tilt")
    for line in result:
        if 'Lord Elements:' in line:
            break
        if line.startswith('#') or not line.strip():
            continue
        p = line.split()
        try:
            idx = int(p[0])
            for e in elems:
                if e['index'] == idx:
                    if len(p) > 5 and p[5] != '---':
                        e['k1'] = float(p[5])
                    if len(p) > 6 and p[6] != '---':
                        e['k2'] = float(p[6])
                    if len(p) > 7 and p[7] != '---':
                        e['ref_tilt'] = float(p[7])
                    break
        except (IndexError, ValueError):
            continue

    # Bend angles
    for e in elems:
        if 'sbend' in e['key'].lower() and e['length'] > 0:
            for line in tao.cmd(f"show element {u_at}{e['index']}"):
                if 'ANGLE' in line and 'rad' in line:
                    try:
                        e['angle'] = float(line.split('=')[1].strip().split()[0])
                        e['raw_angle'] = e['angle']
                    except Exception:
                        pass
                    break

    # Cavity parameters
    for e in elems:
        kl = e['key'].lower()
        if ('rfcavity' in kl or 'lcavity' in kl) and e['length'] > 0:
            for line in tao.cmd(f"show element {u_at}{e['index']}"):
                lu = line.upper()
                if 'VOLTAGE' in lu and '=' in line:
                    try:
                        e['voltage'] = float(line.split('=')[1].strip().split()[0])
                    except Exception:
                        pass
                if 'RF_FREQUENCY' in lu and '=' in line:
                    try:
                        e['frequency'] = float(line.split('=')[1].strip().split()[0])
                    except Exception:
                        pass

    # Twiss + orbit — pipe lat_list for all optics, show lattice for orbit
    try:
        tw_result = tao.cmd(
            f"pipe lat_list {uni_idx}@0>>*|model "
            "ele.ix_ele,ele.a.beta,ele.b.beta,"
            "ele.a.eta,ele.b.eta,"
            "ele.a.phi,ele.b.phi")
        tw_map = {}
        for line in tw_result:
            line = line.strip()
            if not line:
                continue
            p = line.split(';')
            try:
                ei = int(p[0])
                tw_map[ei] = {
                    'beta_x': float(p[1]), 'beta_y': float(p[2]),
                    'eta_x':  float(p[3]), 'eta_y':  float(p[4]),
                    'mu_x':   float(p[5]), 'mu_y':   float(p[6]),
                    'orbit_x': 0.0, 'orbit_y': 0.0,
                }
            except (IndexError, ValueError):
                continue

        # Orbit via show lattice — same approach as 2D plotter
        # Also captures s_end directly from Tao (authoritative s position)
        try:
            orb_lines = tao.cmd(
                f"show lattice {u} -all -att orbit_x -att orbit_y")
            for line in orb_lines:
                if 'Lord Elements:' in line:
                    break
                if line.startswith('#') or not line.strip():
                    continue
                p = line.split()
                try:
                    ei = int(p[0])
                    if ei in tw_map:
                        tw_map[ei]['orbit_x'] = float(p[5]) if len(p) > 5 and p[5] != '---' else 0.0
                        tw_map[ei]['orbit_y'] = float(p[6]) if len(p) > 6 and p[6] != '---' else 0.0
                        tw_map[ei]['s_end']   = float(p[3]) if len(p) > 3 else None
                except (IndexError, ValueError):
                    continue
        except Exception as orb_err:
            L(f"[tao] Orbit query failed ({orb_err}) — orbit set to zero")
        if tw_map:
            L(f"[tao] Twiss loaded: {len(tw_map)} elements")
            for e in elems:
                ei = e['index']
                if ei in tw_map:
                    e.update(tw_map[ei])
    except Exception as tw_err:
        L(f"[tao] Twiss query failed ({tw_err}) — no optics functions")

    # Floor coordinates
    try:
        fp_result = tao.cmd(
            f"pipe lat_list {uni_idx}@0>>*|model "
            "ele.ix_ele,ele.x_position,ele.y_position,ele.z_position,"
            "ele.theta_position,ele.phi_position")
        fp_map = {}
        for line in fp_result:
            line = line.strip()
            if not line:
                continue
            p = line.split(';')
            try:
                ei = int(p[0])
                fp_map[ei] = (float(p[1]), float(p[2]), float(p[3]),
                              float(p[4]), float(p[5]))
            except (IndexError, ValueError):
                continue
        if fp_map:
            L(f"[tao] Floor plan loaded: {len(fp_map)} elements with survey coords")
            for e in elems:
                ei = e['index']
                if ei in fp_map and (ei - 1) in fp_map:
                    x0, y0, z0, th0, ph0 = fp_map[ei - 1]
                    x1, y1, z1, th1, ph1 = fp_map[ei]
                    e['flr_x0'] = x0; e['flr_y0'] = y0; e['flr_z0'] = z0
                    e['flr_x1'] = x1; e['flr_y1'] = y1; e['flr_z1'] = z1
                    e['flr_theta0'] = th0; e['flr_phi0'] = ph0
                    e['flr_theta1'] = th1; e['flr_phi1'] = ph1
    except Exception as fp_err:
        L(f"[tao] Floor plan query failed ({fp_err}) — using dead-reckoning")

    return {'elements': elems}


def load_tao(init_file, log_fn=None, bmad_lib=None, bmad_extra_paths=None):
    def L(m):
        (log_fn(m + '\n') if log_fn else print(m))

    L("[tao] Starting Tao...")
    tao = _make_tao(f"-init {init_file} -noplot",
                     bmad_lib=bmad_lib, bmad_extra_paths=bmad_extra_paths)
    n_uni, uni_labels = _parse_tao_init(init_file)
    L(f"[tao] {n_uni} universe(s): {uni_labels}")
    universes = {}
    for i in range(1, n_uni + 1):
        L(f"[tao] Loading universe {i}: {uni_labels[i]}")
        universes[i] = _load_tao_universe(tao, i, log_fn=log_fn)
    return {
        'universes': universes,
        'universe_labels': uni_labels,
        'n_universes': n_uni,
        'elements': universes[1]['elements'],
    }
