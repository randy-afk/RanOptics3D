"""
ranoptics3d._mesh
=================
3D trace builders: beampipe centerline, Twiss sigma tube,
crosshair lines, and aggregated element Mesh3d groups.
"""
from __future__ import annotations
import numpy as np
from ._elements import (element_color, element_legend, make_hover,
                        FULL_WIDTH_TYPES, THIN_ELEMENT_THRESHOLD,
                        _MARKER_MONITOR_KEYS, _normalize_key)
from ._geometry import (_rot_matrix, _box_mesh, _bend_box_mesh,
                        _ellipsoid_mesh, _box_edges, _octahedron_mesh,
                        _helix_mesh,
                        _aperture_cylinder_mesh, _aperture_block_mesh,
                        _ellipse_edges)

def _build_beampipe_tube(elements, radius=0.03, n_sides=12, color='#888888'):
    """Build a cylindrical tube mesh following the beampipe survey path.

    Connects element entry/exit points with a tube of given radius.
    Returns a dict with Mesh3d data, or None if no floor coords found.
    """
    # Collect path segments from floor coordinates
    path = []
    for e in elements:
        if 'flr_x0' not in e:
            continue
        path.append((
            np.array([e['flr_x0'], e['flr_y0'], e['flr_z0']]),
            np.array([e['flr_x1'], e['flr_y1'], e['flr_z1']]),
            e.get('flr_theta0', 0.0),
            e.get('flr_phi0',   0.0),
        ))

    if not path:
        return None

    # Build tube cross-sections at each unique point along the path
    angles = np.linspace(0, 2 * np.pi, n_sides, endpoint=False)
    all_vx, all_vy, all_vz = [], [], []
    rings = []  # list of (start_idx, n_verts) per ring

    def _add_ring(pt, theta, phi):
        right, up, _ = _rot_matrix(theta, phi)
        start = len(all_vx)
        for a in angles:
            p = pt + radius * (np.cos(a) * np.array(right) +
                               np.sin(a) * np.array(up))
            all_vx.append(float(p[0]))
            all_vy.append(float(p[1]))
            all_vz.append(float(p[2]))
        rings.append(start)

    # First ring at entry of first segment
    _add_ring(path[0][0], path[0][2], path[0][3])
    for p0, p1, th, ph in path:
        _add_ring(p1, th, ph)

    # Faces between consecutive rings
    ii, jj, kk = [], [], []
    for ri in range(len(rings) - 1):
        ra = rings[ri]
        rb = rings[ri + 1]
        for si in range(n_sides):
            sn = (si + 1) % n_sides
            a, b, c, d = ra+si, ra+sn, rb+si, rb+sn
            ii += [a, a]; jj += [b, d]; kk += [c, d]

    return dict(x=all_vx, y=all_vy, z=all_vz, i=ii, j=jj, k=kk, color=color)


def _build_beampipe_trace(elements, color='#888888', width=2):
    """Beampipe centerline: connect element entry/exit points."""
    xs, ys, zs = [], [], []
    for e in elements:
        if 'flr_x0' not in e:
            continue
        xs.extend([e['flr_x0'], e['flr_x1']])
        ys.extend([e['flr_y0'], e['flr_y1']])
        zs.extend([e['flr_z0'], e['flr_z1']])
    if not xs:
        return None
    return dict(x=xs, y=ys, zs=zs, color=color, width=width)


def _build_twiss_tube(elements, emit_x, emit_y, n_phi=16, scale=1.0,
                      auto_scale=True, target_hw=0.2, log_fn=None):
    """Build a Mesh3d elliptical tube showing real beam sigma along beampipe.

    At each element midpoint the cross-section is an ellipse with:
        semi-axis along local 'right' = scale * sqrt(emit_x * beta_x)  (σ_x)
        semi-axis along local 'up'    = scale * sqrt(emit_y * beta_y)  (σ_y)

    auto_scale: if True, automatically multiply by a factor so the median σ
        equals 30% of target_hw (the element half-width). This keeps the tube
        visible regardless of how small the physical emittance is. The scale
        parameter still applies on top of this.
    """
    def L(m):
        if log_fn: log_fn(m + '\n')

    samples = []
    for e in elements:
        if 'flr_x0' not in e:
            continue
        bx = e.get('beta_x', 0.0)
        by = e.get('beta_y', 0.0)
        if bx <= 0 or by <= 0:
            continue
        xm = 0.5 * (e['flr_x0'] + e['flr_x1'])
        ym = 0.5 * (e['flr_y0'] + e['flr_y1'])
        zm = 0.5 * (e['flr_z0'] + e['flr_z1'])
        theta = e.get('flr_theta0', 0.0)
        phi   = e.get('flr_phi0',   0.0)
        right, up, _ = _rot_matrix(theta, phi)
        sx_phys = np.sqrt(emit_x * bx)
        sy_phys = np.sqrt(emit_y * by)
        samples.append((xm, ym, zm, right, up, sx_phys, sy_phys))

    if len(samples) < 2:
        L("[twiss] Not enough beta data for tube — check backend loaded twiss")
        return None

    # Auto-scale: find factor so median sigma = 30% of element half-width
    vis_scale = scale
    if auto_scale:
        all_s = [s for _, _, _, _, _, sx, sy in samples for s in (sx, sy) if s > 0]
        if all_s:
            median_s = float(np.median(all_s))
            if median_s > 0:
                auto_factor = (0.30 * target_hw) / median_s
                vis_scale = scale * auto_factor
                L(f"[twiss] Physical median σ = {median_s*1e3:.3f} mm → "
                  f"auto-scale ×{auto_factor:.1f} → visual σ = "
                  f"{median_s*auto_factor*1e3:.1f} mm")

    L(f"[twiss] Building tube from {len(samples)} sample points "
      f"(vis_scale={vis_scale:.1f})")

    phis = np.linspace(0, 2 * np.pi, n_phi, endpoint=False)
    all_vx, all_vy, all_vz = [], [], []

    for xm, ym, zm, right, up, sx_phys, sy_phys in samples:
        sx = vis_scale * sx_phys
        sy = vis_scale * sy_phys
        for ph in phis:
            vx = xm + right[0] * sx * np.cos(ph) + up[0] * sy * np.sin(ph)
            vy = ym + right[1] * sx * np.cos(ph) + up[1] * sy * np.sin(ph)
            vz = zm + right[2] * sx * np.cos(ph) + up[2] * sy * np.sin(ph)
            all_vx.append(float(vx))
            all_vy.append(float(vy))
            all_vz.append(float(vz))

    n_rings = len(samples)
    ii, jj, kk = [], [], []
    for r in range(n_rings - 1):
        for p in range(n_phi):
            a0 = r * n_phi + p
            a1 = r * n_phi + (p + 1) % n_phi
            b0 = (r + 1) * n_phi + p
            b1 = (r + 1) * n_phi + (p + 1) % n_phi
            ii += [a0, a0]; jj += [a1, b1]; kk += [b0, b1]

    return dict(xs=all_vx, ys=all_vy, zs=all_vz, i=ii, j=jj, k=kk)


def _build_crosshair_lines(elements, emit_x, emit_y, scale=1.0,
                           auto_scale=True, target_hw=0.2, log_fn=None):
    """Build Scatter3d crosshair lines showing σ_x and σ_y at each element.

    Uses the same auto-scale logic as _build_twiss_tube so crosshairs match
    the tube size.
    """
    # Compute auto-scale factor from median sigma
    vis_scale = scale
    if auto_scale:
        all_s = []
        for e in elements:
            bx = e.get('beta_x', 0.0); by = e.get('beta_y', 0.0)
            if bx > 0: all_s.append(np.sqrt(emit_x * bx))
            if by > 0: all_s.append(np.sqrt(emit_y * by))
        if all_s:
            median_s = float(np.median(all_s))
            if median_s > 0:
                vis_scale = scale * (0.30 * target_hw) / median_s

    xs_x, ys_x, zs_x = [], [], []
    xs_y, ys_y, zs_y = [], [], []

    for e in elements:
        if 'flr_x0' not in e:
            continue
        bx = e.get('beta_x', 0.0)
        by = e.get('beta_y', 0.0)
        if bx <= 0 or by <= 0:
            continue
        xm = 0.5 * (e['flr_x0'] + e['flr_x1'])
        ym = 0.5 * (e['flr_y0'] + e['flr_y1'])
        zm = 0.5 * (e['flr_z0'] + e['flr_z1'])
        theta = e.get('flr_theta0', 0.0)
        phi   = e.get('flr_phi0',   0.0)
        right, up, _ = _rot_matrix(theta, phi)
        sx = vis_scale * np.sqrt(emit_x * bx)
        sy = vis_scale * np.sqrt(emit_y * by)

        xs_x += [xm - right[0]*sx, xm + right[0]*sx, None]
        ys_x += [ym - right[1]*sx, ym + right[1]*sx, None]
        zs_x += [zm - right[2]*sx, zm + right[2]*sx, None]

        xs_y += [xm - up[0]*sy, xm + up[0]*sy, None]
        ys_y += [ym - up[1]*sy, ym + up[1]*sy, None]
        zs_y += [zm - up[2]*sy, zm + up[2]*sy, None]

    return (dict(xs=xs_x, ys=ys_x, zs=zs_x),
            dict(xs=xs_y, ys=ys_y, zs=zs_y))


def _build_element_meshes(elements, half_w_default=0.2, half_h_default=0.2,
                          show_markers=False, bend_segments=12, dark_mode=True,
                          show_outlines=True, log_fn=None):
    """Group elements by type and build Mesh3d + outline Scatter3d traces.

    Returns:
        groups   — dict legend_name -> mesh data (for Mesh3d)
        outlines — dict legend_name -> edge line data (for Scatter3d outlines)
        markers  — dict with octahedron mesh data for markers/monitors
    """
    def L(m):
        (log_fn(m + '\n') if log_fn else None)

    groups   = {}  # legend_name -> mesh arrays
    outlines = {}  # legend_name -> edge line arrays
    marker_data = {'xs': [], 'ys': [], 'zs': [], 'i': [], 'j': [], 'k': [],
                   'hover': [], 'color': '#9467bd'}

    def _ensure_group(legend_name, color):
        if legend_name not in groups:
            groups[legend_name] = {
                'color': color,
                'xs': [], 'ys': [], 'zs': [],
                'i': [], 'j': [], 'k': [],
                'hover': [],
            }
            outlines[legend_name] = {
                'color': color,
                'xs': [], 'ys': [], 'zs': [],
            }
        return groups[legend_name], outlines[legend_name]

    def _outline_color(dark_mode):
        """Fixed outline color that contrasts against all element types."""
        return 'rgba(255,255,255,0.30)' if dark_mode else 'rgba(0,0,0,0.30)'

    skipped = 0
    for elem in elements:
        kc = _normalize_key(elem['key'])
        is_marker = any(m in kc for m in _MARKER_MONITOR_KEYS)

        # ── Markers / monitors — octahedron ──────────────────────────────
        if is_marker:
            if not show_markers:
                skipped += 1
                continue
            if 'flr_x0' not in elem:
                continue
            xm = 0.5 * (elem['flr_x0'] + elem['flr_x1'])
            ym = 0.5 * (elem['flr_y0'] + elem['flr_y1'])
            zm = 0.5 * (elem['flr_z0'] + elem['flr_z1'])
            size = half_w_default * 0.5
            vx, vy, vz, oi, oj, ok = _octahedron_mesh(xm, ym, zm, size)
            hover = make_hover(elem)
            offset = len(marker_data['xs'])
            marker_data['xs'].extend(vx); marker_data['ys'].extend(vy)
            marker_data['zs'].extend(vz)
            marker_data['i'].extend([v + offset for v in oi])
            marker_data['j'].extend([v + offset for v in oj])
            marker_data['k'].extend([v + offset for v in ok])
            marker_data['hover'].extend([hover] * len(vx))
            continue

        color = element_color(elem['key'])
        legend = element_legend(elem['key'])
        if color is None or legend is None:
            continue
        L_ = elem['length']
        if L_ < THIN_ELEMENT_THRESHOLD:
            continue
        if 'flr_x0' not in elem:
            continue

        x0 = elem['flr_x0']; y0 = elem['flr_y0']; z0 = elem['flr_z0']
        theta = elem.get('flr_theta0', 0.0)
        phi   = elem.get('flr_phi0',   0.0)

        if any(t in kc for t in FULL_WIDTH_TYPES):
            hw = half_w_default;       hh = half_h_default
        else:
            hw = half_w_default * 0.6; hh = half_h_default * 0.6

        # Magnet size override from file
        if '_mag_hw' in elem:
            hw = elem['_mag_hw']
            hh = elem.get('_mag_hh', hw)

        hover = make_hover(elem)
        g, ol = _ensure_group(legend, color)

        # Cylinder shape override — replaces geometry entirely
        if elem.get('_mag_shape') == 'cylinder':
            xs, ys, zs, ii, jj, kk = _aperture_cylinder_mesh(
                x0, y0, z0, theta, phi, L_, radius=hw, radius_y=hh, caps=True)
            n_vert = len(xs)
            offset = len(g['xs'])
            g['xs'].extend(xs); g['ys'].extend(ys); g['zs'].extend(zs)
            g['i'].extend([v + offset for v in ii])
            g['j'].extend([v + offset for v in jj])
            g['k'].extend([v + offset for v in kk])
            g['hover'].extend([hover] * n_vert)
            ex, ey, ez = _ellipse_edges(x0, y0, z0, theta, phi, L_, hw, hh)
            ol['xs'].extend(ex); ol['ys'].extend(ey); ol['zs'].extend(ez)
            continue

        # ── RF/LC cavity — ellipsoid ──────────────────────────────────────
        if 'rfcavity' in kc or 'lcavity' in kc:
            xs, ys, zs, ii, jj, kk = _ellipsoid_mesh(
                x0, y0, z0, theta, phi, L_, hw, hh)
        elif 'solenoid' in kc:
            xs, ys, zs, ii, jj, kk = _helix_mesh(
                x0, y0, z0, theta, phi, L_,
                coil_r=half_w_default,
                tube_r=half_w_default * 0.15)
        else:
            # ── Dipoles — segmented arc ───────────────────────────────────
            ang = elem.get('angle', 0.0)
            rt  = elem.get('ref_tilt', 0.0)
            is_vbend = abs(abs(rt) - np.pi / 2) < 0.01
            # ELEGANT: positive angle bends toward -x for horizontal dipoles.
            # Negate horizontal only so mesh matches floor plan direction.
            mesh_ang = ang if is_vbend else -ang
            if 'sbend' in kc and abs(ang) > 1e-6:
                xs, ys, zs, ii, jj, kk = _bend_box_mesh(
                    x0, y0, z0, theta, phi, L_, mesh_ang, hw, hh,
                    n_seg=bend_segments, vertical=is_vbend)
                # Per-segment edges following the curved mesh
                seg_len = L_ / bend_segments
                seg_ang = mesh_ang / bend_segments
                cur_x, cur_y, cur_z = x0, y0, z0
                cur_theta, cur_phi = theta, phi
                for seg in range(bend_segments):
                    if is_vbend:
                        mid_phi   = cur_phi + seg_ang / 2.0
                        mid_theta = cur_theta
                    else:
                        mid_theta = cur_theta + seg_ang / 2.0
                        mid_phi   = cur_phi
                    ex, ey, ez = _box_edges(
                        cur_x, cur_y, cur_z, mid_theta, mid_phi,
                        seg_len, hw, hh)
                    ol['xs'].extend(ex); ol['ys'].extend(ey); ol['zs'].extend(ez)
                    _, _, fwd_mid = _rot_matrix(mid_theta, mid_phi)
                    cur_x += fwd_mid[0] * seg_len
                    cur_y += fwd_mid[1] * seg_len
                    cur_z += fwd_mid[2] * seg_len
                    if is_vbend:
                        cur_phi   += seg_ang
                    else:
                        cur_theta += seg_ang
            else:
                xs, ys, zs, ii, jj, kk = _box_mesh(
                    x0, y0, z0, theta, phi, L_, hw, hh)
                # Box edge outlines
                ex, ey, ez = _box_edges(x0, y0, z0, theta, phi, L_, hw, hh)
                ol['xs'].extend(ex); ol['ys'].extend(ey); ol['zs'].extend(ez)

        n_vert = len(xs)

        n_vert = len(xs)
        offset = len(g['xs'])
        g['xs'].extend(xs); g['ys'].extend(ys); g['zs'].extend(zs)
        g['i'].extend([v + offset for v in ii])
        g['j'].extend([v + offset for v in jj])
        g['k'].extend([v + offset for v in kk])
        g['hover'].extend([hover] * n_vert)

    # Set adaptive outline color based on dark/light mode
    ol_color = _outline_color(dark_mode)
    for legend_name in outlines:
        outlines[legend_name]['edge_color'] = ol_color
    if not show_outlines:
        for legend_name in outlines:
            outlines[legend_name]['xs'] = []
            outlines[legend_name]['ys'] = []
            outlines[legend_name]['zs'] = []

    L(f"[3d] Built mesh groups: {list(groups.keys())} ({skipped} markers/monitors hidden)")
    return groups, outlines, marker_data



# ─── Tunnel wall reader ──────────────────────────────────────────────────────

def _read_tunnel_wall(filepath, log_fn=None):
    """Read a tunnel wall coordinate file.

    Format: each row has 6 values (any delimiter):
        x_inner  y_inner  z_inner  x_outer  y_outer  z_outer
    Returns dict with arrays {xi, yi, zi, xo, yo, zo, is_ring}, or None.
    """
    def L(m):
        if log_fn:
            log_fn(m + '\n')

    xi, yi, zi, xo, yo, zo = [], [], [], [], [], []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = re.split(r'[,\t\s]+', line)
                parts = [p for p in parts if p]
                if len(parts) < 6:
                    continue
                try:
                    xi.append(float(parts[0]))
                    yi.append(float(parts[1]))
                    zi.append(float(parts[2]))
                    xo.append(float(parts[3]))
                    yo.append(float(parts[4]))
                    zo.append(float(parts[5]))
                except ValueError:
                    continue
    except Exception as e:
        L(f"[tunnel] Error reading {filepath}: {e}")
        return None

    if len(xi) < 2:
        L(f"[tunnel] Only {len(xi)} valid rows — skipping")
        return None

    xi = np.array(xi); yi = np.array(yi); zi = np.array(zi)
    xo = np.array(xo); yo = np.array(yo); zo = np.array(zo)
    dist = ((xi[0] - xi[-1])**2 + (zi[0] - zi[-1])**2)**0.5
    is_ring = dist < 1e-3
    if is_ring:
        xi = np.append(xi, xi[0]); yi = np.append(yi, yi[0]); zi = np.append(zi, zi[0])
        xo = np.append(xo, xo[0]); yo = np.append(yo, yo[0]); zo = np.append(zo, zo[0])
    L(f"[tunnel] Loaded {len(xi)} wall points (ring={is_ring})")
    return dict(xi=xi, yi=yi, zi=zi, xo=xo, yo=yo, zo=zo, is_ring=is_ring)



# ─── Aperture mesh builder ────────────────────────────────────────────────────

def _build_aperture_meshes(matched, log_fn=None):
    """Build aperture overlay meshes from matched aperture entries.

    matched: list of dicts from match_apertures()
    Returns list of dicts: [{xs, ys, zs, i, j, k, shape}, ...]
    one per matched element that has floor coordinates.
    """
    def L(m):
        if log_fn: log_fn(m + '\n')

    meshes = []
    for m in matched:
        e = m['element']
        if 'flr_x0' not in e:
            continue
        x0    = e['flr_x0']
        y0    = e['flr_y0']
        z0    = e['flr_z0']
        theta = e.get('flr_theta0', 0.0)
        phi   = e.get('flr_phi0',   0.0)
        L_    = float(e.get('length', 0.0))
        if L_ < 1e-9:
            continue

        ox = m['outer_x']
        oy = m['outer_y']

        if m['shape'] == 'cylinder':
            vx, vy, vz, ii, jj, kk = _aperture_cylinder_mesh(
                x0, y0, z0, theta, phi, L_, radius=ox)
        else:
            vx, vy, vz, ii, jj, kk = _aperture_block_mesh(
                x0, y0, z0, theta, phi, L_, ox, oy)

        meshes.append({
            'xs': vx, 'ys': vy, 'zs': vz,
            'i': ii, 'j': jj, 'k': kk,
            'shape': m['shape'],
            'name': e['name'],
        })

    L(f"[aperture] Built {len(meshes)} aperture meshes")
    return meshes
