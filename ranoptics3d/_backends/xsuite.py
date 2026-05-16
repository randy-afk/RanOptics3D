"""
ranoptics3d._backends.xsuite
=============================
xsuite backend — loads via xtrack, calls survey() and twiss().
"""
from __future__ import annotations
from pathlib import Path
import numpy as np

def _key_from_type_xs(etype):
    t = etype.lower()
    if 'bend' in t:
        return 'sbend'
    if 'quadrupole' in t or t == 'quadrupole':
        return 'quadrupole'
    if 'sextupole' in t:
        return 'sextupole'
    if 'multipole' in t:
        return 'quadrupole'
    if 'cavity' in t:
        return 'rfcavity'
    if 'drift' in t:
        return 'drift'
    if 'monitor' in t:
        return 'monitor'
    if 'marker' in t:
        return 'marker'
    if 'kicker' in t or 'hkicker' in t or 'vkicker' in t:
        return 'kicker'
    return 'other'


def load_xsuite(json_file, log_fn=None, line_name=None):
    def L(m):
        (log_fn(m + '\n') if log_fn else print(m))

    try:
        import xtrack as xt
    except ImportError:
        raise SystemExit("[xsuite] not installed → pip install xsuite")

    p = Path(json_file).resolve()
    L(f"[xsuite] Loading lattice from {p.name}")

    line = None
    env = None
    try:
        env = xt.Environment.from_json(str(p))
    except Exception:
        line = xt.Line.from_json(str(p))

    if env is not None:
        names = list(env.lines.keys()) if hasattr(env, 'lines') else []
        if not names:
            raise SystemExit("[xsuite] Environment has no lines.")
        if line_name and line_name in names:
            chosen = line_name
        else:
            chosen = max(names, key=lambda n: len(env[n].element_names))
        L(f"[xsuite] Using line '{chosen}'")
        line = env[chosen]

    if line.particle_ref is None:
        line.particle_ref = xt.Particles(p0c=6500e9, q0=1, mass0=xt.PROTON_MASS_EV)

    line.build_tracker()

    elements = []
    try:
        tab = line.get_table()
        tab_names = list(tab.name) if hasattr(tab, 'name') else []
        tab_types = list(tab.element_type) if hasattr(tab, 'element_type') else []
        tab_s = np.array(tab.s, dtype=float) if hasattr(tab, 's') else np.array([])
        type_map = {str(n): str(t) for n, t in zip(tab_names, tab_types)}

        # Patch np.bool for older xsuite versions
        import numpy as _np_patch
        had_bool = hasattr(_np_patch, 'bool')
        orig_bool = getattr(_np_patch, 'bool', None)

        def _safe_bool(x):
            try:
                a = np.asarray(x)
                if a.ndim == 0:
                    return bool(a.item())
                return bool(a.any())
            except Exception:
                return bool(x)

        _np_patch.bool = _safe_bool
        try:
            sv = line.survey()
        finally:
            if had_bool and orig_bool is not None:
                _np_patch.bool = orig_bool
            else:
                try:
                    del _np_patch.bool
                except Exception:
                    pass

        sv_names = list(sv.name) if hasattr(sv, 'name') else []
        sv_X = np.array(sv.X, dtype=float) if hasattr(sv, 'X') else np.array([])
        sv_Z = np.array(sv.Z, dtype=float) if hasattr(sv, 'Z') else np.array([])
        sv_Y = np.array(sv.Y, dtype=float) if hasattr(sv, 'Y') else np.array([])
        sv_theta = (np.array(sv.theta, dtype=float)
                    if hasattr(sv, 'theta') else np.array([]))
        sv_phi = np.array(sv.phi, dtype=float) if hasattr(sv, 'phi') else np.array([])
        L(f"[xsuite] Survey: {len(sv_names)} points")

        tab_s_list = list(tab_s)
        for i, tname in enumerate(tab_names):
            sname = str(tname)
            etype = type_map.get(sname, '')
            key = _key_from_type_xs(etype)
            s_start = float(tab_s_list[i]) if i < len(tab_s_list) else 0.0
            s_end = float(tab_s_list[i + 1]) if i + 1 < len(tab_s_list) else s_start
            length = s_end - s_start

            k1 = k2 = angle = 0.0
            try:
                el = line[sname]

                def _scalar(v):
                    try:
                        f = float(v) if not hasattr(v, '__len__') else float(v.flat[0])
                        return f if np.isfinite(f) else 0.0
                    except Exception:
                        return 0.0

                if hasattr(el, 'k1'):
                    v = _scalar(el.k1)
                    if v:
                        k1 = v
                if hasattr(el, 'k2'):
                    v = _scalar(el.k2)
                    if v:
                        k2 = v
                if hasattr(el, 'knl') and el.knl is not None:
                    try:
                        if len(el.knl) > 1 and not k1:
                            k1 = _scalar(el.knl[1])
                        if len(el.knl) > 2 and not k2:
                            k2 = _scalar(el.knl[2])
                    except Exception:
                        pass
                if hasattr(el, 'angle'):
                    v = _scalar(el.angle)
                    if v:
                        angle = -v
                elif hasattr(el, 'h'):
                    v = _scalar(el.h)
                    if v:
                        angle = v * length
            except Exception:
                pass

            si = i + 1 if i + 1 < len(sv_names) else i
            si0 = i
            X0 = float(sv_X[si0]) if 0 <= si0 < len(sv_X) else 0.0
            X1 = float(sv_X[si]) if 0 <= si < len(sv_X) else 0.0
            Z0 = float(sv_Z[si0]) if 0 <= si0 < len(sv_Z) else 0.0
            Z1 = float(sv_Z[si]) if 0 <= si < len(sv_Z) else 0.0
            Y0 = float(sv_Y[si0]) if 0 <= si0 < len(sv_Y) else 0.0
            Y1 = float(sv_Y[si]) if 0 <= si < len(sv_Y) else 0.0
            th = float(sv_theta[si0]) if 0 <= si0 < len(sv_theta) else 0.0
            ph = float(sv_phi[si0]) if 0 <= si0 < len(sv_phi) else 0.0

            elements.append({
                'name': sname, 'key': key, 'index': i,
                's_start': s_start, 'length': length,
                'angle': angle, 'raw_angle': angle,
                'k1': k1, 'k2': k2,
                'hkick': 0.0, 'vkick': 0.0, 'kick': 0.0,
                'ref_tilt': 0.0, 'voltage': 0.0, 'frequency': 0.0,
                'flr_z0': Z0, 'flr_x0': X0, 'flr_y0': Y0,
                'flr_z1': Z1, 'flr_x1': X1, 'flr_y1': Y1,
                'flr_theta0': th, 'flr_phi0': ph,
            })
        L(f"[xsuite] Built {len(elements)} elements")

        # Twiss data — beta, dispersion, phase, orbit
        try:
            tw = line.twiss(method='4d')
            tw_names = list(tw.name) if hasattr(tw, 'name') else []
            def _twarr(attr):
                return np.array(getattr(tw, attr), dtype=float) if hasattr(tw, attr) else np.array([])
            tw_betx = _twarr('betx'); tw_bety = _twarr('bety')
            tw_dx   = _twarr('dx');   tw_dy   = _twarr('dy')
            tw_mux  = _twarr('mux');  tw_muy  = _twarr('muy')
            tw_x    = _twarr('x');    tw_y    = _twarr('y')
            tw_map = {}
            for j, nm in enumerate(tw_names):
                tw_map[str(nm).upper()] = {
                    'beta_x':  float(tw_betx[j]) if j < len(tw_betx) else 0.0,
                    'beta_y':  float(tw_bety[j]) if j < len(tw_bety) else 0.0,
                    'eta_x':   float(tw_dx[j])   if j < len(tw_dx)   else 0.0,
                    'eta_y':   float(tw_dy[j])    if j < len(tw_dy)   else 0.0,
                    'mu_x':    float(tw_mux[j])   if j < len(tw_mux)  else 0.0,
                    'mu_y':    float(tw_muy[j])   if j < len(tw_muy)  else 0.0,
                    'orbit_x': float(tw_x[j])     if j < len(tw_x)    else 0.0,
                    'orbit_y': float(tw_y[j])     if j < len(tw_y)    else 0.0,
                }
            for e in elements:
                k = e['name'].upper()
                if k in tw_map:
                    e.update(tw_map[k])
            L(f"[xsuite] Twiss loaded: {len(tw_map)} entries")
        except Exception as tw_err:
            L(f"[xsuite] Twiss failed: {tw_err}")
    except Exception as e:
        L(f"[xsuite] Survey failed: {e}")
        return {'elements': []}

    return {'elements': elements}


