"""
ranoptics3d._backends.elegant
==============================
ELEGANT backend — runs ELEGANT, parses .flr/.twi/.cen SDDS files.
"""
from __future__ import annotations
import os
import re
import subprocess
import tempfile
from pathlib import Path
import numpy as np

def _run_elegant(ele_file, log_fn=None):
    def L(m):
        (log_fn(m + '\n') if log_fn else print(m))

    p = Path(ele_file).resolve()
    rd = p.parent
    L(f"[elegant] Running: elegant {p.name}  (cwd={rd})")
    r = subprocess.run(['elegant', p.name], cwd=str(rd),
                       capture_output=True, text=True)
    if r.returncode != 0:
        L(r.stdout[-2000:]); L(r.stderr[-2000:])
        raise RuntimeError(f"elegant exited with code {r.returncode}")
    L("[elegant] Run complete.")
    return rd


def _find_sdds(run_dir, ext):
    m = list(run_dir.glob(f'*{ext}'))
    if not m:
        raise FileNotFoundError(f"[elegant] No *{ext} file found in {run_dir}")
    m.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return m[0]


def _sdds_to_ascii(sdds_file):
    with open(sdds_file, 'rb') as f:
        h = f.read(300).decode('ascii', errors='ignore')
    if not any(x in h.lower() for x in ('little-endian', 'big-endian', 'mode=binary')):
        return sdds_file, False
    fd, tmp = tempfile.mkstemp(suffix='.sdds_ascii')
    os.close(fd)
    r = subprocess.run(['sddsconvert', sdds_file, tmp, '-ascii'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        os.unlink(tmp)
        raise RuntimeError(f"sddsconvert failed: {r.stderr.strip()}")
    return tmp, True


def _read_sdds(sdds_file, want_cols):
    tmp, is_tmp = _sdds_to_ascii(str(sdds_file))
    try:
        with open(tmp, 'r') as f:
            lines = f.readlines()
        col_names = []; param_names = []; ds = 0
        for i, line in enumerate(lines):
            ls = line.lower()
            if '&parameter' in ls:
                m = re.search(r'name\s*=\s*([\w/]+)', line, re.IGNORECASE)
                if m:
                    param_names.append(m.group(1))
            elif '&column' in ls:
                m = re.search(r'name\s*=\s*([\w/]+)', line, re.IGNORECASE)
                if m:
                    col_names.append(m.group(1))
            elif '&data' in ls:
                ds = i + 1
                break
        skip = ds + len(param_names)
        if skip < len(lines) and lines[skip].strip().isdigit():
            skip += 1
        ci = {n: i for i, n in enumerate(col_names) if n in set(want_cols)}
        data = {c: [] for c in want_cols}
        for line in lines[skip:]:
            line = line.strip()
            if not line or line.startswith('!'):
                continue
            parts = line.split()
            if len(parts) < len(col_names):
                continue
            for col, idx in ci.items():
                v = parts[idx]
                try:
                    data[col].append(float(v))
                except Exception:
                    data[col].append(v)
        return data
    finally:
        if is_tmp:
            os.unlink(tmp)


def _read_lte(lte_file):
    with open(str(lte_file), 'r') as f:
        content = f.read()
    clean = []
    for line in content.splitlines():
        if '!' in line:
            line = line[:line.index('!')]
        line = line.strip()
        if line:
            clean.append(line)
    text = ' '.join(clean)
    elems = {}
    for m in re.finditer(
            r'(\w+)\s*:\s*(\w+)\s*(?:,\s*)?([^:]*?)(?=\s+\w+\s*:|$)',
            text, re.DOTALL):
        name = m.group(1).strip().upper()
        etype = m.group(2).strip().upper()
        ps = m.group(3) or ''
        e = {'type': etype, 'K1': 0.0, 'K2': 0.0, 'ANGLE': 0.0,
             'KICK': 0.0, 'HKICK': 0.0, 'VKICK': 0.0,
             'VOLT': 0.0, 'FREQ': 0.0, 'TILT': 0.0}
        for pm in re.finditer(r'(\w+)\s*=\s*([+-]?[\d.eE+-]+)', ps):
            pn = pm.group(1).upper()
            try:
                val = float(pm.group(2))
            except Exception:
                continue
            if pn in e:
                e[pn] = val
        elems[name] = e
    return elems


def _key_from_type_elegant(etype):
    r = etype.upper()
    if r in ('CSBEND', 'SBEND', 'RBEN', 'RBEND', 'SBEN', 'CSRCSBEND', 'KSBEND'):
        return 'SBend'
    if r in ('KQUAD', 'QUAD', 'QUADRUPOLE', 'KQUSE'):
        return 'Quadrupole'
    if r in ('KSEXT', 'SEXT', 'SEXTUPOLE'):
        return 'Sextupole'
    if r in ('HKICK', 'EHKICK'):
        return 'Hkicker'
    if r in ('VKICK', 'EVKICK'):
        return 'Vkicker'
    if r in ('KICKER', 'EKICKER', 'HVCORRECTOR'):
        return 'Kicker'
    if r in ('MONI', 'MONITOR', 'HMON', 'VMON'):
        return 'Monitor'
    if r in ('MARK', 'MARKER'):
        return 'Marker'
    if r in ('RFCA', 'RFCW', 'RFDF', 'RFTMEZ0', 'RFTM110', 'MODRF', 'RFMODE'):
        return 'RFcavity'
    return etype.capitalize()


def load_elegant(ele_file, log_fn=None):
    def L(m):
        (log_fn(m + '\n') if log_fn else print(m))

    ep = Path(ele_file).resolve()
    run_dir = _run_elegant(ele_file, log_fn)
    lte_file = ep.parent / (ep.stem + '.lte')
    if not lte_file.exists():
        try:
            with open(str(ep), 'r') as f:
                for line in f:
                    m = re.search(r'lattice\s*=\s*["\']?([^\s,"\'&]+)',
                                  line, re.IGNORECASE)
                    if m:
                        lte_file = ep.parent / m.group(1).strip()
                        break
        except Exception:
            pass
    lte_data = {}
    if lte_file.exists():
        L(f"[elegant] Reading lattice from {lte_file.name}")
        lte_data = _read_lte(str(lte_file))

    elements = []
    try:
        flr = _read_sdds(str(_find_sdds(run_dir, '.flr')),
                         ['s', 'ds', 'Z', 'X', 'Y', 'theta', 'phi',
                          'ElementName', 'ElementType'])
        fnames = flr.get('ElementName', [])
        ftypes = flr.get('ElementType', [])
        fs = [float(v) for v in flr.get('s', [])]
        fds = [float(v) for v in flr.get('ds', [])]
        fZ = [float(v) for v in flr.get('Z', [])]
        fX = [float(v) for v in flr.get('X', [])]
        fY = [float(v) for v in flr.get('Y', [])] if flr.get('Y') else []
        fth = [float(v) for v in flr.get('theta', [])]
        fph = [float(v) for v in flr.get('phi', [])] if flr.get('phi') else []
        for i, name in enumerate(fnames):
            etype = str(ftypes[i]) if i < len(ftypes) else ''
            ds_v  = fds[i] if i < len(fds) else 0.0
            s_end = fs[i]  if i < len(fs)  else 0.0
            # Use the previous element's exit s as s_start, NOT s_end - ds.
            # ds in the .flr file is the floor-plan path step, which for some
            # elements (e.g. a quad immediately after a drift) inherits the
            # drift's step length rather than the quad's actual length, causing
            # element overlap. Computing from the previous row's s guarantees
            # each element starts exactly where the previous one ended.
            s_prev   = fs[i - 1] if i > 0 and i - 1 < len(fs) else 0.0
            s_start  = s_prev
            length   = s_end - s_prev   # actual element length
            Z1 = fZ[i] if i < len(fZ) else 0.0
            X1 = fX[i] if i < len(fX) else 0.0
            Y1 = fY[i] if i < len(fY) else 0.0
            key = _key_from_type_elegant(etype)
            le = lte_data.get(str(name).upper(), {})
            Z0 = fZ[i - 1] if i > 0 and i - 1 < len(fZ) else Z1
            X0 = fX[i - 1] if i > 0 and i - 1 < len(fX) else X1
            Y0 = fY[i - 1] if i > 0 and i - 1 < len(fY) else Y1
            th = fth[i - 1] if i > 0 and i - 1 < len(fth) else 0.0
            phi = fph[i - 1] if i > 0 and i - 1 < len(fph) else 0.0
            elements.append({
                'name': str(name), 'key': key, 'index': i,
                's_start': s_start, 'length': length,
                'flr_length': ds_v,   # raw .flr path step, preserved for geometry use
                'angle': le.get('ANGLE', 0.0),
                'raw_angle': le.get('ANGLE', 0.0),
                'k1': le.get('K1', 0.0), 'k2': le.get('K2', 0.0),
                'hkick': le.get('HKICK', 0.0), 'vkick': le.get('VKICK', 0.0),
                'kick': le.get('KICK', 0.0), 'ref_tilt': le.get('TILT', 0.0),
                'voltage': le.get('VOLT', 0.0), 'frequency': le.get('FREQ', 0.0),
                'flr_z0': Z0, 'flr_x0': X0, 'flr_y0': Y0,
                'flr_z1': Z1, 'flr_x1': X1, 'flr_y1': Y1,
                'flr_theta0': th, 'flr_phi0': phi,
            })
    except FileNotFoundError:
        L("[elegant] No .flr file found.")
        L("  → Add &floor_coordinates filename=\"%s.flr\" &end to your .ele")
        return {'elements': []}
    # Twiss + orbit data — parse .twi and .cen SDDS files
    try:
        twi_file = _find_sdds(run_dir, '.twi')
        twi = _read_sdds(str(twi_file),
                         ['s', 'betax', 'betay', 'etax', 'etay',
                          'psix', 'psiy', 'ElementName'])
        def _tcol(key):
            return [float(v) for v in twi.get(key, [])]
        twi_nm  = [str(v) for v in twi.get('ElementName', [])]
        twi_bx = _tcol('betax'); twi_by = _tcol('betay')
        twi_ex = _tcol('etax');  twi_ey = _tcol('etay')
        twi_mx = _tcol('psix');  twi_my = _tcol('psiy')
        twi_map = {}
        for j, nm in enumerate(twi_nm):
            twi_map[nm.upper()] = {
                'beta_x': twi_bx[j] if j < len(twi_bx) else 0.0,
                'beta_y': twi_by[j] if j < len(twi_by) else 0.0,
                'eta_x':  twi_ex[j] if j < len(twi_ex) else 0.0,
                'eta_y':  twi_ey[j] if j < len(twi_ey) else 0.0,
                'mu_x':   twi_mx[j] if j < len(twi_mx) else 0.0,
                'mu_y':   twi_my[j] if j < len(twi_my) else 0.0,
            }
        for e in elements:
            k = e['name'].upper()
            if k in twi_map:
                e.update(twi_map[k])
        L(f"[elegant] Twiss loaded from {twi_file.name}: {len(twi_map)} entries")
    except FileNotFoundError:
        L("[elegant] No .twi file found — no optics functions. "
          "Add &twiss_output filename=\"%s.twi\" &end to your .ele")
    except Exception as tw_err:
        L(f"[elegant] Twiss parse failed: {tw_err}")

    # Orbit from .cen file (centroid)
    try:
        cen_file = _find_sdds(run_dir, '.cen')
        cen = _read_sdds(str(cen_file), ['Cx', 'Cy', 'ElementName'])
        cen_nm = [str(v) for v in cen.get('ElementName', [])]
        cen_cx = [float(v) for v in cen.get('Cx', [])]
        cen_cy = [float(v) for v in cen.get('Cy', [])]
        cen_map = {}
        for j, nm in enumerate(cen_nm):
            cen_map[nm.upper()] = (
                cen_cx[j] if j < len(cen_cx) else 0.0,
                cen_cy[j] if j < len(cen_cy) else 0.0,
            )
        for e in elements:
            k = e['name'].upper()
            if k in cen_map:
                e['orbit_x'] = cen_map[k][0]
                e['orbit_y'] = cen_map[k][1]
        L(f"[elegant] Orbit loaded from {cen_file.name}: {len(cen_map)} entries")
    except FileNotFoundError:
        L("[elegant] No .cen file found — no orbit data. "
          "Add &bunched_beam_moments filename=\"%s.cen\" &end to your .ele")
    except Exception as ce:
        L(f"[elegant] Orbit parse failed: {ce}")

    return {'elements': elements}