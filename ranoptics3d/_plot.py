"""
ranoptics3d._plot
=================
Core plotting function plot_optics_3d() plus utility helpers:
range filter, annotation builder, element stats, focus/camera.
"""
from __future__ import annotations
import re
import fnmatch
from pathlib import Path
import numpy as np
import plotly.graph_objects as go

from ._elements  import element_color, element_legend, make_hover, _MARKER_MONITOR_KEYS
from ._geometry  import _rot_matrix
from ._mesh      import (_build_beampipe_trace, _build_beampipe_tube,
                         _build_twiss_tube,
                         _build_crosshair_lines, _build_element_meshes,
                         _build_aperture_meshes)
from ._aperture  import parse_aperture_file, match_apertures
from ._backends  import load_tao, load_elegant, load_xsuite, load_madx
from ._panel.builder import build_control_panel

def _find_element_position(elements, name):
    """Return (x, y, z, length) at the midpoint of the element matching name.

    Matches case-insensitively, exact name first then unique prefix.
    Returns None if not found or no survey coords.
    """
    if not name:
        return None
    target = name.strip().upper()

    def _midpoint(e):
        if 'flr_x0' not in e:
            return None
        xm = 0.5 * (e['flr_x0'] + e['flr_x1'])
        ym = 0.5 * (e['flr_y0'] + e['flr_y1'])
        zm = 0.5 * (e['flr_z0'] + e['flr_z1'])
        return (xm, ym, zm, e.get('length', 0.0))

    # Exact match first
    for e in elements:
        ename = e['name'].split('\\')[-1].upper()
        if ename == target:
            r = _midpoint(e)
            if r is not None:
                return r
    # Unique prefix fallback (skip if multiple)
    matches = []
    for e in elements:
        ename = e['name'].split('\\')[-1].upper()
        if ename.startswith(target):
            r = _midpoint(e)
            if r is not None:
                matches.append((e['name'], r))
    if len(matches) == 1:
        return matches[0][1]
    return None


def _parse_camera_eye(spec):
    """Parse a camera eye spec like '1.5,1.2,1.5' into a dict, or None."""
    if not spec or not spec.strip():
        return None
    parts = re.split(r'[,\s]+', spec.strip())
    parts = [p for p in parts if p]
    if len(parts) != 3:
        return None
    try:
        return dict(x=float(parts[0]), y=float(parts[1]), z=float(parts[2]))
    except ValueError:
        return None


# ─── Element statistics ──────────────────────────────────────────────────────

def compute_lattice_stats(elements):
    """Return a dict of element counts and total length."""
    counts = {}
    total = 0.0
    for e in elements:
        kc = e['key'].lower()
        L_ = e.get('length', 0.0)
        total = max(total, e.get('s_start', 0.0) + L_)
        if 'sbend' in kc or 'rbend' in kc:
            counts['Dipoles'] = counts.get('Dipoles', 0) + 1
        elif 'quadrupole' in kc:
            counts['Quadrupoles'] = counts.get('Quadrupoles', 0) + 1
        elif 'sextupole' in kc:
            counts['Sextupoles'] = counts.get('Sextupoles', 0) + 1
        elif 'octupole' in kc:
            counts['Octupoles'] = counts.get('Octupoles', 0) + 1
        elif kc in ('kicker', 'hkicker', 'vkicker'):
            counts['Kickers'] = counts.get('Kickers', 0) + 1
        elif 'monitor' in kc or 'instrument' in kc:
            counts['Monitors'] = counts.get('Monitors', 0) + 1
        elif 'rfcavity' in kc or 'lcavity' in kc:
            counts['RF Cavities'] = counts.get('RF Cavities', 0) + 1
        elif 'marker' in kc:
            counts['Markers'] = counts.get('Markers', 0) + 1
    return {'counts': counts, 'total_length': total, 'n_elements': len(elements)}


# ─── Range filter ────────────────────────────────────────────────────────────

def _filter_by_range(elements, srange):
    """Filter elements to a sub-range expressed as 'START:END'.
    START/END can be either element names or s values."""
    if not srange:
        return elements
    pts = srange.split(':')
    if len(pts) != 2:
        raise ValueError(f"Invalid range '{srange}'. Use START:END.")

    def _resolve(tok):
        try:
            return float(tok)
        except ValueError:
            tu = tok.upper()
            for e in elements:
                if e['name'].upper() == tu:
                    return e['s_start']
            raise ValueError(f"Element '{tok}' not found.")

    s_lo = _resolve(pts[0].strip())
    s_hi = _resolve(pts[1].strip())
    if s_lo > s_hi:
        s_lo, s_hi = s_hi, s_lo
    return [e for e in elements
            if (e['s_start'] + e['length']) >= s_lo and e['s_start'] <= s_hi]


# ─── Annotation builder ──────────────────────────────────────────────────────

def _build_annotations(elements, pattern):
    """Return a list of (x, y, z, text) for elements matching the pattern.
    Pattern is a comma-separated wildcard string (e.g. 'IPM*, BPM*')."""
    import fnmatch
    if not pattern or not pattern.strip():
        return []
    patterns = [p.strip() for p in pattern.split(',') if p.strip()]
    if not patterns:
        return []
    seen = set()
    out = []
    for e in elements:
        if 'flr_x0' not in e:
            continue
        name = e['name'].split('\\')[-1]
        if not any(fnmatch.fnmatch(name.upper(), p.upper()) for p in patterns):
            continue
        xm = 0.5 * (e['flr_x0'] + e['flr_x1'])
        ym = 0.5 * (e['flr_y0'] + e['flr_y1'])
        zm = 0.5 * (e['flr_z0'] + e['flr_z1'])
        key = (round(xm, 6), round(ym, 6), round(zm, 6))
        if key in seen:
            continue
        seen.add(key)
        out.append((xm, ym, zm, name))
    return out


def plot_optics_3d(
    input_file,
    code='auto',
    output_file='optics3d.html',
    title=None,
    flip_bend=False,
    element_half_width=0.2,
    element_half_height=0.2,
    show_beampipe=True,
    show_outlines=True,        # show white edge outlines on elements
    aperture_file=None,        # path to magnet size definition file
    beampipe_color='#888888',
    beampipe_width=2,
    show_markers=False,
    bend_segments=12,
    dark_mode=True,
    show=False,
    universes=None,
    xsuite_line=None,
    madx_survey=None,
    aspect='data',  # 'data' preserve proportions, 'cube' equal, 'manual' use scale_*
    scale_x=1.0, scale_y=1.0, scale_z=1.0,
    srange=None,
    visible_types=None,
    type_opacity=None,
    annotation_pattern=None,
    annotation_font_size=10,
    tunnel_wall_file=None,
    show_tunnel=False,
    show_ground=False,
    ground_y=0.0,
    ground_grid=True,
    show_axes_gizmo=True,
    z_up=False,
    camera_preset='iso',
    camera_eye=None,           # custom eye position dict {x,y,z}; overrides preset
    focus_element=None,        # element name to center rotation pivot on
    focus_radius=None,         # if set, also crops view to a window of this radius
    add_control_panel=True,    # inject in-browser interactive control panel
    emit_x=None,               # geometric horizontal emittance (m·rad)
    emit_y=None,               # geometric vertical emittance (m·rad)
    sigma_dp=None,             # momentum spread δp/p (not yet used in tube)
    show_twiss=True,           # show Twiss sigma tube when emittance is set
    twiss_scale=1.0,           # visual multiplier (1=1σ, 3=3σ envelope)
    twiss_n_phi=16,            # azimuthal segments on tube cross-section
    twiss_tube_opacity=0.35,   # tube mesh opacity
    twiss_x_color='#74c0fc',   # βx tube / crosshair color (blue)
    twiss_y_color='#69db7c',   # βy tube / crosshair color (green)
    inspector_plots=None,      # list of plots to show: 'beta','sigma','dispersion','orbit','phase'
    phase_normalized=False,    # True = phase in units of 2π (0→1), False = cumulative radians
    log_fn=None,
):
    """Build a 3D HTML plot of an accelerator lattice.

    Parameters
    ----------
    input_file          : path to lattice file (.init / .ele / .json / .tfs)
    code                : 'auto', 'tao', 'elegant', 'xsuite', or 'madx'
    output_file         : output HTML path
    title               : plot title (optional)
    flip_bend           : mirror x to flip bend direction
    element_half_width  : half-width of element boxes (m)
    element_half_height : half-height of element boxes (m)
    show_beampipe       : draw beampipe centerline
    beampipe_color      : line color for beampipe
    beampipe_width      : line width for beampipe
    show_markers        : include markers/monitors as boxes
    bend_segments       : number of sub-boxes per bend (smoothness)
    dark_mode           : dark or light theme
    show                : open in browser after writing
    universes           : list of universe indices (Tao multi-universe)
    xsuite_line         : line name inside an xsuite Environment JSON
    madx_survey         : path to MAD-X survey.tfs
    aspect              : 'data' (real proportions), 'cube' (equal axes),
                          or 'manual' (use scale_x/y/z)
    scale_x, scale_y, scale_z : axis scale ratios when aspect='manual'.
                          Each scale acts as a multiplier on that axis's real
                          data extent. scale=1 shows real proportion; scale<1
                          compresses; scale>1 stretches. Example: a lattice
                          10 m wide × 80 m long with scale_x=1, scale_z=0.5
                          renders as if Z were 40 m, halving its visual length.
    srange              : 'START:END' range filter (element names or s values)
    visible_types       : iterable of legend names to show; None = all
    type_opacity        : dict legend_name -> 0..1 opacity
    annotation_pattern  : wildcard pattern for element name labels in 3D
    annotation_font_size: font size for annotations
    tunnel_wall_file    : optional tunnel wall coordinate file
    show_tunnel         : draw tunnel wall mesh
    show_ground         : draw ground plane at y=ground_y
    ground_y            : y coordinate of the ground plane
    ground_grid         : draw a grid on the ground plane
    show_axes_gizmo     : draw a small XYZ axes gizmo at origin
    z_up                : use Z-up convention (default Y-up)
    camera_preset       : 'iso','top','side','front','free'
    camera_eye          : dict {x,y,z} overriding the preset eye position.
                          Use this to reproduce a specific camera state from
                          a previous browser session.
    focus_element       : element name (e.g. 'IP1', 'QF12'). Centers the
                          rotation pivot on this element, so dragging in the
                          browser rotates around it instead of the scene
                          center. Case-insensitive; falls back to unique
                          prefix match.
    focus_radius        : if set (in meters), additionally crops the visible
                          axis ranges to focus_element ± focus_radius. Use
                          this for "zoom to selection" behavior.
    add_control_panel   : if True (default), embeds a live HTML control panel
                          in the output: type visibility/opacity, click-to-
                          focus, camera presets, aspect sliders, live
                          annotation pattern, pinned info readout. The panel
                          is pure HTML+JS, no server required.
    log_fn              : optional logging function
    """
    import plotly.graph_objects as go

    if inspector_plots is None:
        inspector_plots = ['beta', 'sigma']

    def L(m):
        (log_fn(m + '\n') if log_fn else print(m))

    # ── Auto-detect code ─────────────────────────────────────────────────────
    if code == 'auto':
        ext = Path(input_file).suffix.lower()
        code = {'.init': 'tao', '.ele': 'elegant',
                '.json': 'xsuite', '.tfs': 'madx'}.get(ext)
        if code is None:
            raise SystemExit(f"Cannot auto-detect code from extension '{ext}'.")
        L(f"[auto] Detected code: {code}")

    # ── Load lattice ─────────────────────────────────────────────────────────
    code = code.lower()
    if code == 'tao':
        data = load_tao(input_file, log_fn=log_fn)
    elif code == 'elegant':
        data = load_elegant(input_file, log_fn=log_fn)
    elif code == 'xsuite':
        data = load_xsuite(input_file, log_fn=log_fn, line_name=xsuite_line)
    elif code == 'madx':
        data = load_madx(input_file, survey_file=madx_survey, log_fn=log_fn)
    else:
        raise ValueError(f"Unknown code '{code}'")

    all_uni = data.get('universes', {1: {'elements': data.get('elements', [])}})
    uni_labels = data.get('universe_labels', {1: 'u1'})
    if universes:
        plot_unis = [u for u in universes if u in all_uni]
    else:
        plot_unis = list(all_uni.keys())
    multi = len(plot_unis) > 1

    # ── Magnet size override ──────────────────────────────────────────────────
    # Parse magnet size file and tag matching elements with _mag_hw/_mag_hh
    # BEFORE the universe loop so mesh building picks them up.
    if aperture_file:
        try:
            import fnmatch as _fnmatch
            entries = parse_aperture_file(aperture_file)
            n_matched = 0
            for uid in plot_unis:
                for e in all_uni[uid]['elements']:
                    ename = e['name'].split('\\')[-1].upper()
                    for entry in entries:
                        if _fnmatch.fnmatch(ename, entry['pattern'].upper()):
                            default_cm = element_half_width * 100.0
                            ox = (entry['outer_x'] if entry['outer_x'] is not None
                                  else default_cm) / 100.0
                            oy = (entry['outer_y'] if entry['outer_y'] is not None
                                  else ox) / 100.0 if entry['outer_y'] is not None else ox
                            e['_mag_hw']    = ox
                            e['_mag_hh']    = oy
                            e['_mag_shape'] = entry['shape']
                            n_matched += 1
                            break
            L(f"[magnet size] {n_matched} elements sized from {aperture_file}")
        except Exception as ap_err:
            L(f"[magnet size] Failed to load file: {ap_err}")

    # ── Optional tunnel wall ─────────────────────────────────────────────────
    tunnel = None
    if show_tunnel and tunnel_wall_file:
        tunnel = _read_tunnel_wall(tunnel_wall_file, log_fn=log_fn)

    # ── Build figure ─────────────────────────────────────────────────────────
    fig = go.Figure()
    all_x, all_y, all_z = [], [], []
    annotations_3d = []

    # Bookkeeping for the in-browser control panel
    type_traces = {}      # legend_name -> list of trace name strings
    type_colors = {}      # legend_name -> hex color (for swatches)
    overlay_traces = {    # overlay name -> list of trace name strings
        'Beampipe': [], 'Tunnel': [], 'Ground': [], 'Axes gizmo': [],
        'Twiss tube': [], 'Twiss σ_x': [], 'Twiss σ_y': [],
    }
    panel_elements = []   # list of {name, x, y, z} for autocomplete + click
    optics_series  = {}   # ulabel -> {s, beta_x, beta_y, eta_x, eta_y, mu_x, mu_y, orbit_x, orbit_y}
                          # parallel arrays straight from the backend, no element matching

    for ui, uid in enumerate(plot_unis):
        uelems = all_uni[uid]['elements']
        ulabel = uni_labels.get(uid, f'u{uid}')

        # Range filter
        try:
            uelems = _filter_by_range(uelems, srange)
        except ValueError as e:
            L(f"[range] {e}")

        # Optional flip
        if flip_bend:
            uelems = [
                {**e,
                 'flr_x0': -e.get('flr_x0', 0.0),
                 'flr_x1': -e.get('flr_x1', 0.0),
                 'flr_theta0': -e.get('flr_theta0', 0.0),
                 'angle': -e.get('angle', 0.0)}
                for e in uelems
            ]

        # Collect raw parallel optics arrays — s1 and optics values in element order.
        # This preserves the exact ordering from the backend (no name matching,
        # no midpoint interpolation) matching how the 2D plotter works.
        ops = {
            's':       [], 'beta_x': [], 'beta_y': [],
            'eta_x':   [], 'eta_y':  [],
            'mu_x':    [], 'mu_y':   [],
            'orbit_x': [], 'orbit_y': [],
            'key':     [], 's0': [],    's1': [],
            'k1':      [], 'angle':  [], 'ref_tilt': [],
            'name':    [],
        }
        for e in uelems:
            if e.get('beta_x', 0.0) <= 0:
                continue
            # Use s_end from Tao directly (authoritative) if available,
            # otherwise fall back to s_start + length
            s1v = float(e.get('s_end', e['s_start'] + e.get('length', 0.0)))
            ops['s'].append(s1v)
            ops['s0'].append(float(e['s_start']))
            ops['s1'].append(s1v)
            ops['beta_x'].append(float(e.get('beta_x', 0.0)))
            ops['beta_y'].append(float(e.get('beta_y', 0.0)))
            ops['eta_x'].append(float(e.get('eta_x',  0.0)))
            ops['eta_y'].append(float(e.get('eta_y',  0.0)))
            ops['mu_x'].append(float(e.get('mu_x',   0.0)))
            ops['mu_y'].append(float(e.get('mu_y',   0.0)))
            ops['orbit_x'].append(float(e.get('orbit_x', 0.0)))
            ops['orbit_y'].append(float(e.get('orbit_y', 0.0)))
            ops['key'].append(e['key'])
            ops['k1'].append(float(e.get('k1', 0.0)))
            ops['angle'].append(float(e.get('angle', 0.0)))
            ops['ref_tilt'].append(float(e.get('ref_tilt', 0.0)))
            ops['name'].append(e['name'].split('\\')[-1])
        optics_series[ulabel] = ops
        # panel_elements: floor-coord elements only, for 3D click/highlight/autocomplete.
        # Optics data for inspector comes from optics_series.
        for e in uelems:
            if 'flr_x0' not in e:
                continue
            kc = e['key'].lower()
            if not show_markers and any(m in kc for m in _MARKER_MONITOR_KEYS):
                continue
            ename = e['name'].split('\\')[-1]
            display_name = ename if not multi else f'{ename} ({ulabel})'
            xm = 0.5 * (e['flr_x0'] + e['flr_x1'])
            ym = 0.5 * (e['flr_y0'] + e['flr_y1'])
            zm = 0.5 * (e['flr_z0'] + e['flr_z1'])
            panel_elements.append({
                'name': display_name,
                'x':    float(xm), 'y': float(ym), 'z': float(zm),
                's0':   float(e['s_start']),
                's1':   float(e['s_start'] + e.get('length', 0.0)),
            })

        # Beampipe
        if show_beampipe:
            bp = _build_beampipe_trace(uelems, color=beampipe_color,
                                       width=beampipe_width)
            if bp:
                bp_label = 'Beampipe' if not multi else f'Beampipe ({ulabel})'
                fig.add_trace(go.Scatter3d(
                    x=bp['x'], y=bp['y'], z=bp['zs'],
                    mode='lines',
                    line=dict(color=beampipe_color, width=bp['width']),
                    name=bp_label,
                    showlegend=True,
                    hoverinfo='skip',
                ))
                overlay_traces['Beampipe'].append(bp_label)
                all_x.extend(bp['x']); all_y.extend(bp['y']); all_z.extend(bp['zs'])

        # Twiss sigma tube / crosshairs
        if show_twiss and emit_x is not None and emit_y is not None:
            ex = float(emit_x); ey = float(emit_y)
            has_beta = any(e.get('beta_x', 0) > 0 for e in uelems)
            if not has_beta:
                L(f"[twiss] No beta data found in universe {uid} — "
                  "ensure backend loaded twiss (check log above)")
            else:
                # Elliptical tube surface
                tube = _build_twiss_tube(
                    uelems, ex, ey,
                    n_phi=twiss_n_phi,
                    scale=twiss_scale,
                    auto_scale=True,
                    target_hw=element_half_width,
                    log_fn=log_fn)
                if tube:
                    tname = 'σ tube' if not multi else f'σ tube ({ulabel})'
                    fig.add_trace(go.Mesh3d(
                        x=tube['xs'], y=tube['ys'], z=tube['zs'],
                        i=tube['i'], j=tube['j'], k=tube['k'],
                        color=twiss_x_color,
                        opacity=twiss_tube_opacity,
                        flatshading=False,
                        name=tname,
                        showlegend=True,
                        hoverinfo='skip',
                        lighting=dict(ambient=0.7, diffuse=0.6,
                                      specular=0.1, roughness=0.8),
                    ))
                    overlay_traces['Twiss tube'].append(tname)
                    all_x.extend(tube['xs'])
                    all_y.extend(tube['ys'])
                    all_z.extend(tube['zs'])

                # Crosshair lines: σ_x (right axis) and σ_y (up axis)
                ch_x, ch_y = _build_crosshair_lines(
                    uelems, ex, ey, scale=twiss_scale,
                    auto_scale=True, target_hw=element_half_width,
                    log_fn=log_fn)
                if ch_x['xs']:
                    cx_name = 'σ_x' if not multi else f'σ_x ({ulabel})'
                    fig.add_trace(go.Scatter3d(
                        x=ch_x['xs'], y=ch_x['ys'], z=ch_x['zs'],
                        mode='lines',
                        line=dict(color=twiss_x_color, width=2),
                        name=cx_name, showlegend=True, hoverinfo='skip',
                    ))
                    overlay_traces['Twiss σ_x'].append(cx_name)
                if ch_y['xs']:
                    cy_name = 'σ_y' if not multi else f'σ_y ({ulabel})'
                    fig.add_trace(go.Scatter3d(
                        x=ch_y['xs'], y=ch_y['ys'], z=ch_y['zs'],
                        mode='lines',
                        line=dict(color=twiss_y_color, width=2),
                        name=cy_name, showlegend=True, hoverinfo='skip',
                    ))
                    overlay_traces['Twiss σ_y'].append(cy_name)
                L(f"[twiss] Tube + crosshairs built "
                  f"(εx={ex:.2e}, εy={ey:.2e}, scale={twiss_scale})")

        # Element meshes
        groups, outlines, marker_data = _build_element_meshes(
            uelems,
            half_w_default=element_half_width,
            half_h_default=element_half_height,
            show_markers=show_markers,
            bend_segments=bend_segments,
            dark_mode=dark_mode,
            show_outlines=show_outlines,
            log_fn=log_fn,
        )

        for legend_name, g in groups.items():
            if not g['xs']:
                continue
            if visible_types is not None and legend_name not in visible_types:
                continue
            display_name = legend_name if not multi else f'{legend_name} ({ulabel})'
            opacity = 1.0
            if type_opacity and legend_name in type_opacity:
                try:
                    opacity = float(type_opacity[legend_name])
                except (ValueError, TypeError):
                    opacity = 1.0
                opacity = max(0.0, min(1.0, opacity))

            fig.add_trace(go.Mesh3d(
                x=g['xs'], y=g['ys'], z=g['zs'],
                i=g['i'], j=g['j'], k=g['k'],
                color=g['color'],
                opacity=opacity,
                flatshading=False,
                name=display_name,
                showlegend=True,
                hovertext=g['hover'],
                hoverinfo='text',
                lighting=dict(ambient=0.4, diffuse=0.9, specular=0.4,
                              roughness=0.3, fresnel=0.2),
                lightposition=dict(x=2000, y=3000, z=4000),
            ))
            type_traces.setdefault(legend_name, []).append(display_name)
            type_colors[legend_name] = g['color']
            all_x.extend(g['xs']); all_y.extend(g['ys']); all_z.extend(g['zs'])

            # Box edge outlines — one Scatter3d per type, aggregated
            ol = outlines.get(legend_name)
            if ol and ol['xs']:
                ol_name = f'{display_name} edges'
                fig.add_trace(go.Scatter3d(
                    x=ol['xs'], y=ol['ys'], z=ol['zs'],
                    mode='lines',
                    line=dict(color=ol['edge_color'], width=1),
                    name=ol_name,
                    showlegend=False,
                    hoverinfo='skip',
                ))
                # Group outline traces with their parent type for visibility toggling
                type_traces.setdefault(legend_name, [])
                if ol_name not in type_traces[legend_name]:
                    type_traces[legend_name].append(ol_name)

        # Markers / monitors — octahedron mesh
        if show_markers and marker_data['xs']:
            mk_label = 'Monitor' if not multi else f'Monitor ({ulabel})'
            fig.add_trace(go.Mesh3d(
                x=marker_data['xs'], y=marker_data['ys'], z=marker_data['zs'],
                i=marker_data['i'], j=marker_data['j'], k=marker_data['k'],
                color=marker_data['color'],
                opacity=0.9,
                flatshading=True,
                name=mk_label,
                showlegend=True,
                hovertext=marker_data['hover'],
                hoverinfo='text',
                lighting=dict(ambient=0.6, diffuse=0.8, specular=0.2,
                              roughness=0.4, fresnel=0.1),
                lightposition=dict(x=1000, y=2000, z=3000),
            ))
            type_traces.setdefault('Monitor', []).append(mk_label)
            type_colors['Monitor'] = marker_data['color']
            all_x.extend(marker_data['xs'])
            all_y.extend(marker_data['ys'])
            all_z.extend(marker_data['zs'])

        # 3D annotations on this universe
        if annotation_pattern:
            annots = _build_annotations(uelems, annotation_pattern)
            for x, y, z, name in annots:
                annotations_3d.append(dict(
                    x=x, y=y, z=z, text=name,
                    showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1,
                    ax=0, ay=-25,
                    font=dict(size=annotation_font_size,
                              color='#FFFFFF' if dark_mode else '#222'),
                    bgcolor='rgba(0,0,0,0.5)' if dark_mode else 'rgba(255,255,255,0.7)',
                    bordercolor='#888', borderwidth=1, borderpad=2,
                ))

    # ── Tunnel wall mesh ─────────────────────────────────────────────────────
    if tunnel is not None:
        # Inner wall as line, outer wall as line, and connecting strip
        fig.add_trace(go.Scatter3d(
            x=tunnel['xi'], y=tunnel['yi'], z=tunnel['zi'],
            mode='lines',
            line=dict(color='rgba(150,150,170,0.7)', width=2, dash='dot'),
            name='Tunnel inner', showlegend=True, hoverinfo='skip',
        ))
        fig.add_trace(go.Scatter3d(
            x=tunnel['xo'], y=tunnel['yo'], z=tunnel['zo'],
            mode='lines',
            line=dict(color='rgba(150,150,170,0.7)', width=2, dash='dot'),
            name='Tunnel outer', showlegend=False, hoverinfo='skip',
        ))
        overlay_traces['Tunnel'].extend(['Tunnel inner', 'Tunnel outer'])
        all_x.extend(np.concatenate([tunnel['xi'], tunnel['xo']]))
        all_y.extend(np.concatenate([tunnel['yi'], tunnel['yo']]))
        all_z.extend(np.concatenate([tunnel['zi'], tunnel['zo']]))

    # ── Compute extents ───────────────────────────────────────────────────────
    if all_x:
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        z_min, z_max = min(all_z), max(all_z)
        dx = (x_max - x_min) or 1.0
        dy = (y_max - y_min) or 1.0
        dz = (z_max - z_min) or 1.0
        pad = 0.05
        xr = [x_min - pad * dx, x_max + pad * dx]
        yr = [y_min - pad * dy, y_max + pad * dy]
        zr = [z_min - pad * dz, z_max + pad * dz]
    else:
        xr = yr = zr = [-1, 1]
        dx = dy = dz = 2.0
        x_min = y_min = z_min = -1
        x_max = y_max = z_max = 1

    # ── Ground plane ─────────────────────────────────────────────────────────
    if show_ground:
        # Plane at y=ground_y spanning x and z extents (y is up by default)
        gx_lo, gx_hi = xr[0], xr[1]
        gz_lo, gz_hi = zr[0], zr[1]
        # Mesh3d quad as two triangles
        gxs = [gx_lo, gx_hi, gx_hi, gx_lo]
        gys = [ground_y] * 4
        gzs = [gz_lo, gz_lo, gz_hi, gz_hi]
        fig.add_trace(go.Mesh3d(
            x=gxs, y=gys, z=gzs,
            i=[0, 0], j=[1, 2], k=[2, 3],
            color='#444' if dark_mode else '#ccc',
            opacity=0.25, flatshading=True,
            name='Ground', showlegend=True, hoverinfo='skip',
        ))
        overlay_traces['Ground'].append('Ground')
        if ground_grid:
            n_lines = 20
            xs_g = np.linspace(gx_lo, gx_hi, n_lines)
            zs_g = np.linspace(gz_lo, gz_hi, n_lines)
            grid_x = []; grid_y = []; grid_z = []
            for xv in xs_g:
                grid_x.extend([xv, xv, None])
                grid_y.extend([ground_y, ground_y, None])
                grid_z.extend([gz_lo, gz_hi, None])
            for zv in zs_g:
                grid_x.extend([gx_lo, gx_hi, None])
                grid_y.extend([ground_y, ground_y, None])
                grid_z.extend([zv, zv, None])
            fig.add_trace(go.Scatter3d(
                x=grid_x, y=grid_y, z=grid_z,
                mode='lines',
                line=dict(color='rgba(120,120,120,0.5)', width=1),
                name='Ground grid', showlegend=False, hoverinfo='skip',
            ))
            overlay_traces['Ground'].append('Ground grid')

    # ── Axes gizmo at origin ────────────────────────────────────────────────
    if show_axes_gizmo and all_x:
        gizmo_len = 0.05 * max(dx, dy, dz)
        for axis_name, color, dirvec in [
            ('X', '#ff5555', (1, 0, 0)),
            ('Y', '#55ff55', (0, 1, 0)),
            ('Z', '#5599ff', (0, 0, 1)),
        ]:
            fig.add_trace(go.Scatter3d(
                x=[0, gizmo_len * dirvec[0]],
                y=[0, gizmo_len * dirvec[1]],
                z=[0, gizmo_len * dirvec[2]],
                mode='lines+text',
                line=dict(color=color, width=5),
                text=['', axis_name],
                textfont=dict(size=12, color=color),
                textposition='middle right',
                name=f'Axis {axis_name}', showlegend=False, hoverinfo='skip',
            ))
            overlay_traces['Axes gizmo'].append(f'Axis {axis_name}')

    # ── Focus / crop on element ───────────────────────────────────────────────
    # When focus_radius is set, crop the view to a window around the element.
    # Highlighting is handled in-browser via the JS panel.
    if focus_element and focus_radius is not None and focus_radius > 0:
        all_elems = []
        for uid in plot_unis:
            all_elems.extend(all_uni[uid]['elements'])
        focus_pos = _find_element_position(all_elems, focus_element)
        if focus_pos is None:
            L(f"[focus] Element '{focus_element}' not found — ignoring.")
        else:
            fx, fy, fz, _ = focus_pos
            r = float(focus_radius)
            xr = [fx - r, fx + r]
            yr = [fy - r, fy + r]
            zr = [fz - r, fz + r]
            dx = dy = dz = 2 * r
            L(f"[focus] View cropped to ±{r} m around '{focus_element}' "
              f"at ({fx:.3f}, {fy:.3f}, {fz:.3f})")

    # ── Theme ────────────────────────────────────────────────────────────────
    if dark_mode:
        bg = '#1e1e1e'; grid = '#444'; tick = '#bbb'; back = '#2a2a2a'
    else:
        bg = '#ffffff'; grid = '#ccc'; tick = '#333'; back = '#f6f6f6'

    # ── Aspect ratio ─────────────────────────────────────────────────────────
    if aspect == 'data':
        # Real proportions: each axis sized by its data extent
        m = max(dx, dy, dz)
        ar = dict(x=dx / m, y=dy / m, z=dz / m)
        aspectmode = 'manual'
    elif aspect == 'manual':
        # Manual: user-supplied scales act as multipliers on the data extent.
        # scale=1 means "show this axis at its real proportion"; scale=0.5
        # squishes that axis to half its real length. Final ratio is normalized
        # so the largest effective axis = 1 (Plotly displays this fine).
        ex = dx * float(scale_x)
        ey = dy * float(scale_y)
        ez = dz * float(scale_z)
        m = max(ex, ey, ez) or 1.0
        ar = dict(x=ex / m, y=ey / m, z=ez / m)
        aspectmode = 'manual'
    else:
        # Cube: force equal axes regardless of data
        ar = dict(x=1, y=1, z=1)
        aspectmode = 'cube'

    # ── Camera preset ────────────────────────────────────────────────────────
    if z_up:
        up_vec = dict(x=0, y=0, z=1)
        # In Z-up worlds, "top" looks down -Z, "front" looks along +Y, etc.
        _cams = {
            'iso':   dict(x=1.6, y=-1.6, z=1.4),
            'top':   dict(x=0,   y=0,    z=2.5),
            'side':  dict(x=2.5, y=0,    z=0.0),  # along +X
            'front': dict(x=0,   y=2.5,  z=0.0),  # along +Y
            'free':  dict(x=1.6, y=-1.6, z=1.4),
        }
    else:
        up_vec = dict(x=0, y=1, z=0)
        _cams = {
            'iso':   dict(x=-0.880, y=0.738, z=-0.772),
            'top':   dict(x=0,      y=2.5,   z=0.001),
            'side':  dict(x=2.5,    y=0,     z=0),
            'front': dict(x=0,      y=0,     z=2.5),
            'free':  dict(x=-0.880, y=0.738, z=-0.772),
        }
    eye = camera_eye if camera_eye else _cams.get(camera_preset, _cams['iso'])

    # camera.center stays at {0,0,0} — focus is achieved by shifting axis ranges
    center = dict(x=0, y=0, z=0)

    fig.update_layout(
        title=dict(text=title or f'RanOptics3D — {Path(input_file).name}',
                   x=0.5, xanchor='center'),
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        font=dict(color=tick),
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor=back,
                       gridcolor=grid, color=tick, range=xr,
                       showspikes=False),
            yaxis=dict(title='Y (m)', backgroundcolor=back,
                       gridcolor=grid, color=tick, range=yr,
                       showspikes=False),
            zaxis=dict(title='Z (m)', backgroundcolor=back,
                       gridcolor=grid, color=tick, range=zr,
                       showspikes=False),
            aspectmode=aspectmode,
            aspectratio=ar,
            camera=dict(eye=eye, up=up_vec, center=center),
            annotations=annotations_3d if annotations_3d else None,
        ),
        legend=dict(
            x=0.99, y=0.95, xanchor='right', yanchor='top',
            bgcolor='rgba(0,0,0,0.4)' if dark_mode else 'rgba(255,255,255,0.7)',
            bordercolor=grid, borderwidth=1,
            itemsizing='constant',
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=900,
    )


    # ── Write ────────────────────────────────────────────────────────────────
    if add_control_panel:
        # Filter overlay_traces to only include kinds that have at least one
        # trace, so the panel doesn't show empty sections.
        overlay_traces = {k: v for k, v in overlay_traces.items() if v}
        scene_data = {
            'elements':       panel_elements,
            'type_traces':    type_traces,
            'type_colors':    type_colors,
            'overlay_traces': overlay_traces,
            'axis_ranges':    {'x': list(xr), 'y': list(yr), 'z': list(zr)},
            'axis_halfext':   {'x': (xr[1]-xr[0])/2,
                               'y': (yr[1]-yr[0])/2,
                               'z': (zr[1]-zr[0])/2},
            'aspect_ratio':   ar,
            'data_extent':    {'x': float(dx), 'y': float(dy), 'z': float(dz)},
            'eyes':           _cams,
            'dark_mode':      bool(dark_mode),
            'annot_font_size': int(annotation_font_size),
            'emit_x':         float(emit_x) if emit_x is not None else None,
            'emit_y':         float(emit_y) if emit_y is not None else None,
            'inspector_plots': inspector_plots,
            'phase_normalized': phase_normalized,
            'optics_series':   optics_series,
        }
        panel_html, panel_js = build_control_panel(scene_data, dark_mode=dark_mode)
        # Build the full HTML to a buffer first, then splice in our panel
        # and our own <script> tag. We don't use Plotly's post_script param
        # because some Plotly versions apply str.format() to it, which would
        # corrupt the embedded JSON's curly braces.
        import io
        buf = io.StringIO()
        fig.write_html(buf, full_html=True, include_plotlyjs='cdn')
        html_text = buf.getvalue()
        injection = (panel_html
                     + '\n<script type="text/javascript">\n'
                     + panel_js
                     + '\n</script>\n')
        if '</body>' in html_text:
            html_text = html_text.replace('</body>', injection + '</body>')
        else:
            html_text += injection
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_text)
    else:
        fig.write_html(output_file)
    L(f"✓ Saved 3D HTML → {output_file}")
    if show:
        import webbrowser
        webbrowser.open(f"file://{Path(output_file).resolve()}")
    return fig


