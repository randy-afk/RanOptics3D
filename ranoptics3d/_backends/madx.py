"""
ranoptics3d._backends.madx
===========================
MAD-X backend — reads twiss TFS + optional survey TFS.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np

def _read_tfs(filepath):
    scalars = {}
    col_names = []
    data = {}
    with open(filepath, 'r') as f:
        lines = f.readlines()
    for line in lines:
        line = line.rstrip('\n')
        if not line.strip():
            continue
        if line.startswith('@'):
            parts = line.split()
            if len(parts) >= 3:
                name = parts[1].upper()
                val_str = parts[-1].strip('"')
                try:
                    scalars[name] = float(val_str)
                except ValueError:
                    scalars[name] = val_str
            continue
        if line.startswith('*'):
            col_names = line[1:].split()
            for c in col_names:
                data[c] = []
            continue
        if line.startswith('$'):
            continue
        if not col_names:
            continue
        tokens = []
        i = 0
        s = line.strip()
        while i < len(s):
            if s[i] == '"':
                j = s.index('"', i + 1)
                tokens.append(s[i + 1:j])
                i = j + 1
            elif s[i] == ' ':
                i += 1
            else:
                j = i
                while j < len(s) and s[j] != ' ':
                    j += 1
                tokens.append(s[i:j])
                i = j
        for ci, col in enumerate(col_names):
            if ci < len(tokens):
                val = tokens[ci]
                try:
                    data[col].append(float(val))
                except ValueError:
                    data[col].append(val)
            else:
                data[col].append(None)
    return scalars, col_names, data


def _key_from_type_madx(keyword):
    k = keyword.upper()
    if k in ('SBEND', 'RBEND', 'DIPEDGE'):
        return 'sbend'
    if k == 'QUADRUPOLE':
        return 'quadrupole'
    if k == 'SEXTUPOLE':
        return 'sextupole'
    if k == 'OCTUPOLE':
        return 'octupole'
    if k in ('HKICKER', 'VKICKER', 'KICKER', 'TKICKER'):
        return 'kicker'
    if k in ('MONITOR', 'HMONITOR', 'VMONITOR', 'INSTRUMENT', 'BPM'):
        return 'monitor'
    if k == 'MARKER':
        return 'marker'
    if k == 'RFCAVITY':
        return 'rfcavity'
    if k == 'LCAVITY':
        return 'lcavity'
    return 'drift'


def load_madx(twiss_file, survey_file=None, log_fn=None):
    def L(m):
        (log_fn(m + '\n') if log_fn else print(m))

    L(f"[madx] Reading twiss: {twiss_file}")
    _, _, twi = _read_tfs(twiss_file)

    def _arr(key):
        vals = twi.get(key.upper(), twi.get(key, []))
        return np.array([v if v is not None else 0.0 for v in vals], dtype=float)

    s = _arr('S'); L_ = _arr('L')
    n = len(s)
    L(f"[madx] Twiss: {n} elements")

    names = twi.get('NAME', twi.get('name', [None] * n))
    keywords = twi.get('KEYWORD', twi.get('keyword', ['DRIFT'] * n))
    k1l_arr = _arr('K1L'); k2l_arr = _arr('K2L')
    ang_arr = _arr('ANGLE'); tilt_arr = _arr('TILT')
    hkick_arr = _arr('HKICK'); vkick_arr = _arr('VKICK')

    betx_arr = _arr('BETX'); bety_arr = _arr('BETY')
    dx_arr   = _arr('DX');   dy_arr   = _arr('DY')
    mux_arr  = _arr('MUX');  muy_arr  = _arr('MUY')
    ox_arr   = _arr('X');    oy_arr   = _arr('Y')

    elements = []
    for i in range(n):
        name = str(names[i]) if names[i] is not None else f'e{i}'
        keyword = str(keywords[i]) if keywords[i] is not None else 'DRIFT'
        key = _key_from_type_madx(keyword)
        length = float(L_[i])
        s_end = float(s[i])
        s_start = s_end - length
        angle = float(ang_arr[i])
        k1 = float(k1l_arr[i]) / length if length > 1e-6 else 0.0
        k2 = float(k2l_arr[i]) / length if length > 1e-6 else 0.0
        e = {
            'name': name, 'key': keyword.capitalize(), 'index': i,
            's_start': s_start, 'length': length,
            'angle': angle, 'raw_angle': angle,
            'k1': k1, 'k2': k2,
            'hkick': float(hkick_arr[i]), 'vkick': float(vkick_arr[i]),
            'kick': float(hkick_arr[i]) if key == 'kicker' else 0.0,
            'ref_tilt': float(tilt_arr[i]),
            'voltage': 0.0, 'frequency': 0.0,
        }
        if i < len(betx_arr) and betx_arr[i] > 0:
            e['beta_x']  = float(betx_arr[i])
            e['beta_y']  = float(bety_arr[i])
            e['eta_x']   = float(dx_arr[i])  if i < len(dx_arr)  else 0.0
            e['eta_y']   = float(dy_arr[i])   if i < len(dy_arr)   else 0.0
            e['mu_x']    = float(mux_arr[i])  if i < len(mux_arr)  else 0.0
            e['mu_y']    = float(muy_arr[i])  if i < len(muy_arr)  else 0.0
            e['orbit_x'] = float(ox_arr[i])   if i < len(ox_arr)   else 0.0
            e['orbit_y'] = float(oy_arr[i])   if i < len(oy_arr)   else 0.0
        elements.append(e)

    if survey_file:
        L(f"[madx] Reading survey: {survey_file}")
        try:
            _, _, sv = _read_tfs(survey_file)
            sv_X = [v if v is not None else 0.0
                    for v in sv.get('X', sv.get('x', []))]
            sv_Y = [v if v is not None else 0.0
                    for v in sv.get('Y', sv.get('y', []))]
            sv_Z = [v if v is not None else 0.0
                    for v in sv.get('Z', sv.get('z', []))]
            sv_theta = [v if v is not None else 0.0
                        for v in sv.get('THETA', sv.get('theta', []))]
            sv_phi = [v if v is not None else 0.0
                      for v in sv.get('PHI', sv.get('phi', []))]
            for i, e in enumerate(elements):
                if i >= len(sv_Z):
                    break
                si = i; si0 = i - 1 if i > 0 else i
                e['flr_z0'] = float(sv_Z[si0]); e['flr_z1'] = float(sv_Z[si])
                e['flr_x0'] = float(sv_X[si0]); e['flr_x1'] = float(sv_X[si])
                e['flr_y0'] = float(sv_Y[si0]); e['flr_y1'] = float(sv_Y[si])
                e['flr_theta0'] = float(sv_theta[si0])
                e['flr_phi0'] = float(sv_phi[si0])
        except Exception as e:
            L(f"[madx] Survey failed: {e}")
    else:
        L("[madx] No survey file — floor plan unavailable")

    return {'elements': elements}

