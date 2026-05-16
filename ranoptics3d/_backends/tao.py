"""
ranoptics3d._backends.tao
=========================
Tao / Bmad backend — loads lattice via pytao.
"""
from __future__ import annotations
import re
from pathlib import Path
import numpy as np

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


def load_tao(init_file, log_fn=None):
    def L(m):
        (log_fn(m + '\n') if log_fn else print(m))

    from pytao import Tao
    L("[tao] Starting Tao...")
    tao = Tao(f"-init {init_file} -noplot")
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
