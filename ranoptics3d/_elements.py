"""
ranoptics3d._elements
=====================
Element styling, hover tooltip builder, and type classification.
"""
from __future__ import annotations
import numpy as np

# Color scheme matches RanOptics 2D floor plan
_ELEMENT_COLORS = {
    'sbend':       '#d62728',  # red
    'rbend':       '#d62728',
    'quadrupole':  '#1f77b4',  # blue
    'sextupole':   '#2ca02c',  # green
    'octupole':    '#9467bd',  # purple
    'kicker':      '#ff7f0e',  # orange
    'hkicker':     '#ff7f0e',
    'vkicker':     '#ff7f0e',
    'monitor':     '#9467bd',  # purple
    'instrument':  '#9467bd',
    'rfcavity':    '#17becf',  # cyan
    'lcavity':     '#17becf',
    'solenoid':    '#e377c2',  # pink/magenta
    'marker':      '#888888',  # gray
}

_ELEMENT_LEGEND_NAME = {
    'sbend': 'Dipole', 'rbend': 'Dipole',
    'quadrupole': 'Quadrupole',
    'sextupole': 'Sextupole', 'octupole': 'Octupole',
    'kicker': 'Kicker', 'hkicker': 'Kicker', 'vkicker': 'Kicker',
    'monitor': 'Monitor', 'instrument': 'Monitor',
    'rfcavity': 'RF Cavity', 'lcavity': 'RF Cavity',
    'solenoid': 'Solenoid',
    'marker': 'Marker',
}

FULL_WIDTH_TYPES = ('sbend', 'rbend', 'quadrupole')
THIN_ELEMENT_THRESHOLD = 1e-3
_MARKER_MONITOR_KEYS = {'marker', 'monitor', 'hmon', 'vmon', 'instrument', 'bpm'}


_KEY_ALIASES = {
    'sole':       'solenoid',
    'drif':       'drift',
    'sben':       'sbend',
    'rben':       'rbend',
    'quad':       'quadrupole',
    'sext':       'sextupole',
    'octu':       'octupole',
    'rfca':       'rfcavity',
    'lcav':       'lcavity',
    'kick':       'kicker',
    'hkic':       'hkicker',
    'vkic':       'vkicker',
    'moni':       'monitor',
    'inst':       'instrument',
    'mark':       'marker',
}

def _normalize_key(key):
    """Normalize element key — handles ELEGANT's 4-char truncated names."""
    k = key.lower().strip()
    return _KEY_ALIASES.get(k, k)


def element_color(key):
    k = _normalize_key(key)
    for prefix, color in _ELEMENT_COLORS.items():
        if prefix in k:
            return color
    return None


def element_legend(key):
    k = _normalize_key(key)
    for prefix, name in _ELEMENT_LEGEND_NAME.items():
        if prefix in k:
            return name
    return None


def make_hover(elem):
    """Build the hover tooltip HTML for one element."""
    name = elem['name'].split('\\')[-1]
    key = elem['key']
    L = elem['length']
    k1 = elem.get('k1', 0.0)
    k2 = elem.get('k2', 0.0)
    angle = elem.get('angle', 0.0)
    raw_angle = elem.get('raw_angle', angle)
    s0 = elem['s_start']
    kc = _normalize_key(key)
    lines = [
        f'<b>{name}</b>',
        f'<i>{key}</i>',
        f'L = {L:.4f} m',
        f's_start = {s0:.4f} m',
        f's_end &nbsp;= {s0 + L:.4f} m',
    ]
    if 'sbend' in kc or 'rbend' in kc:
        rt = elem.get('ref_tilt', 0.0)
        bend_plane = 'Vertical' if abs(abs(rt) - np.pi / 2) < 0.01 else 'Horizontal'
        lines.append(f'Bend plane: {bend_plane}')
        lines.append(f'Angle = {np.degrees(raw_angle):.4f}°')
        if abs(raw_angle) > 1e-9:
            lines.append(f'ρ = {abs(L / raw_angle):.4f} m')
    if 'quadrupole' in kc:
        lines.append(f'K1 = {k1:.6f} m⁻²')
    if 'sextupole' in kc:
        lines.append(f'K2 = {k2:.6f} m⁻³')
    if kc == 'kicker':
        lines += [
            f'hkick = {elem.get("hkick", 0):.6f}',
            f'vkick = {elem.get("vkick", 0):.6f}',
        ]
    elif kc in ('hkicker', 'vkicker'):
        lines.append(f'kick = {elem.get("kick", 0):.6f}')
    if 'rfcavity' in kc or 'lcavity' in kc:
        v = elem.get('voltage', 0.0)
        f = elem.get('frequency', 0.0)
        if v:
            lines.append(f'V = {v / 1e6:.3f} MV' if abs(v) >= 1e6 else f'V = {v:.1f} V')
        if f:
            lines.append(f'f = {f / 1e9:.4f} GHz' if f >= 1e9 else f'f = {f / 1e6:.4f} MHz')
    # Position info for 3D
    if 'flr_x0' in elem:
        x0 = elem['flr_x0']; y0 = elem['flr_y0']; z0 = elem['flr_z0']
        lines.append(f'pos = ({x0:.3f}, {y0:.3f}, {z0:.3f})')
    return '<br>'.join(lines) + '<extra></extra>'


# ─── 3D box geometry ─────────────────────────────────────────────────────────

def _rot_matrix(theta, phi):
    """Rotation: first phi (pitch about local x), then theta (yaw about world y).

    Beam direction in Bmad floor convention:
        +z (theta=0, phi=0) is the reference forward direction.
        theta rotates in the x-z plane (positive theta turns toward +x — but
        the actual sign convention is handled by sin(theta)/cos(theta) below).
        phi tilts the beam upward (+y) when positive.

    For consistency with the survey output of pytao/ELEGANT/xsuite we use:
        forward = ( sin(theta)*cos(phi),  sin(phi),  cos(theta)*cos(phi) )
    """
    cph = np.cos(phi); sph = np.sin(phi)
    cth = np.cos(theta); sth = np.sin(theta)
    # forward axis (along beam)
    fx = sth * cph
    fy = sph
    fz = cth * cph
    # local up axis (perpendicular to forward, in vertical plane)
    ux = -sth * sph
    uy = cph
    uz = -cth * sph
    # local right axis (forward × up — use cross product, signs follow Bmad)
    rx = cth
    ry = 0.0
    rz = -sth
    return np.array([rx, ry, rz]), np.array([ux, uy, uz]), np.array([fx, fy, fz])


def _box_mesh(x0, y0, z0, theta, phi, length, half_w, half_h):
    """Return (xs, ys, zs, i, j, k) for a Plotly Mesh3d box.

    The box starts at (x0, y0, z0), extends `length` along the beam direction,
    half_w to either side (transverse horizontal in beam frame),
    half_h above/below (transverse vertical in beam frame).
    """
    right, up, fwd = _rot_matrix(theta, phi)
    # 8 corners: 4 at entry face, 4 at exit face
    p0 = np.array([x0, y0, z0])
    p1 = p0 + fwd * length
    corners = []
    for base in (p0, p1):
        for sw, sh in ((-1, -1), (+1, -1), (+1, +1), (-1, +1)):
            corners.append(base + right * (sw * half_w) + up * (sh * half_h))
    corners = np.array(corners)  # shape (8, 3)
    # Triangle faces — 12 triangles (2 per face × 6 faces)
    # Vertex indices: 0-3 = entry face (CCW from outside), 4-7 = exit face
    faces = [
        # Entry face (looking back along +fwd, so reversed winding for outward normal)
        (0, 2, 1), (0, 3, 2),
        # Exit face
        (4, 5, 6), (4, 6, 7),
        # Right side (sw=+1)
        (1, 2, 6), (1, 6, 5),
        # Left side (sw=-1)
        (0, 4, 7), (0, 7, 3),
        # Top (sh=+1)
        (3, 7, 6), (3, 6, 2),
        # Bottom (sh=-1)
        (0, 1, 5), (0, 5, 4),
    ]
    xs = corners[:, 0].tolist()
    ys = corners[:, 1].tolist()
    zs = corners[:, 2].tolist()
    i = [f[0] for f in faces]
    j = [f[1] for f in faces]
    k = [f[2] for f in faces]
    return xs, ys, zs, i, j, k


def _bend_box_mesh(x0, y0, z0, theta0, phi0, length, angle,
                   half_w, half_h, n_seg=12, vertical=False):
    """Segmented box mesh for a bending dipole.

    Subdivides the bend into n_seg straight sub-boxes that follow the arc.
    Returns the same (xs, ys, zs, i, j, k) tuple format as _box_mesh.
    """
    if abs(angle) < 1e-9 or n_seg < 1:
        return _box_mesh(x0, y0, z0, theta0, phi0, length, half_w, half_h)

    seg_len = length / n_seg
    seg_ang = angle / n_seg
    xs, ys, zs = [], [], []
    i_idx, j_idx, k_idx = [], [], []
    cur_x, cur_y, cur_z = x0, y0, z0
    cur_theta = theta0
    cur_phi = phi0

    for seg in range(n_seg):
        # Mid-segment angle for orientation (so the box is centered on the arc)
        if vertical:
            mid_phi = cur_phi + seg_ang / 2.0
            mid_theta = cur_theta
        else:
            mid_theta = cur_theta + seg_ang / 2.0
            mid_phi = cur_phi
        # Build one sub-box
        sub_xs, sub_ys, sub_zs, si, sj, sk = _box_mesh(
            cur_x, cur_y, cur_z, mid_theta, mid_phi, seg_len, half_w, half_h)
        offset = len(xs)
        xs.extend(sub_xs); ys.extend(sub_ys); zs.extend(sub_zs)
        i_idx.extend([v + offset for v in si])
        j_idx.extend([v + offset for v in sj])
        k_idx.extend([v + offset for v in sk])
        # Advance current position to end of sub-box arc (not straight-line end)
        if vertical:
            # Curve in y-z plane (or y-forward plane)
            _, _, fwd_end = _rot_matrix(mid_theta, cur_phi + seg_ang)
            _, _, fwd_mid = _rot_matrix(mid_theta, mid_phi)
            # Approximate position advance using mid-direction × seg_len
            cur_x += fwd_mid[0] * seg_len
            cur_y += fwd_mid[1] * seg_len
            cur_z += fwd_mid[2] * seg_len
            cur_phi += seg_ang
        else:
            _, _, fwd_mid = _rot_matrix(mid_theta, mid_phi)
            cur_x += fwd_mid[0] * seg_len
            cur_y += fwd_mid[1] * seg_len
            cur_z += fwd_mid[2] * seg_len
            cur_theta += seg_ang

    return xs, ys, zs, i_idx, j_idx, k_idx


# ─── Ellipsoid (RF cavity) mesh ──────────────────────────────────────────────

def _ellipsoid_mesh(x0, y0, z0, theta, phi, length, half_w, half_h,
                    n_lat=8, n_lon=12):
    """Approximate ellipsoid mesh for RF/LC cavities.

    The ellipsoid has semi-axes: length/2 along beam, half_w transverse horizontal,
    half_h transverse vertical.  Built in local frame then rotated.
    """
    right, up, fwd = _rot_matrix(theta, phi)
    cx = x0 + fwd[0] * length / 2
    cy = y0 + fwd[1] * length / 2
    cz = z0 + fwd[2] * length / 2
    a = length / 2      # along beam
    b = half_w          # transverse horizontal
    c = half_h          # transverse vertical

    verts = []
    for i in range(n_lat + 1):
        lat = np.pi * i / n_lat - np.pi / 2          # -pi/2 .. pi/2
        cl = np.cos(lat); sl = np.sin(lat)
        for j in range(n_lon):
            lon = 2 * np.pi * j / n_lon
            # Local ellipsoid coords
            lx = a * sl                               # along beam axis
            ly = b * cl * np.cos(lon)                 # transverse right
            lz = c * cl * np.sin(lon)                 # transverse up
            # Rotate into world frame
            wx = cx + lx * fwd[0] + ly * right[0] + lz * up[0]
            wy = cy + lx * fwd[1] + ly * right[1] + lz * up[1]
            wz = cz + lx * fwd[2] + ly * right[2] + lz * up[2]
            verts.append((wx, wy, wz))

    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]

    ii, jj, kk = [], [], []
    for i in range(n_lat):
        for j in range(n_lon):
            a0 = i * n_lon + j
            a1 = i * n_lon + (j + 1) % n_lon
            b0 = (i + 1) * n_lon + j
            b1 = (i + 1) * n_lon + (j + 1) % n_lon
            ii += [a0, a0]; jj += [a1, b0]; kk += [b0, b1]

    return xs, ys, zs, ii, jj, kk


# ─── Box edge outlines ───────────────────────────────────────────────────────

def _box_edges(x0, y0, z0, theta, phi, length, half_w, half_h):
    """Return (xs, ys, zs) line segments for the 12 edges of a box.

    Uses None separators so all edges can be concatenated into one Scatter3d.
    """
    right, up, fwd = _rot_matrix(theta, phi)
    p0 = np.array([x0, y0, z0])
    p1 = p0 + fwd * length
    corners = []
    for base in (p0, p1):
        for sw, sh in ((-1, -1), (+1, -1), (+1, +1), (-1, +1)):
            corners.append(base + right * (sw * half_w) + up * (sh * half_h))
    # 12 edges: 4 on entry face, 4 on exit face, 4 longitudinal
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),   # entry face
        (4, 5), (5, 6), (6, 7), (7, 4),   # exit face
        (0, 4), (1, 5), (2, 6), (3, 7),   # longitudinal
    ]
    xs, ys, zs = [], [], []
    for a, b in edges:
        xs += [corners[a][0], corners[b][0], None]
        ys += [corners[a][1], corners[b][1], None]
        zs += [corners[a][2], corners[b][2], None]
    return xs, ys, zs


# ─── Octahedron (marker/monitor) mesh ────────────────────────────────────────

def _octahedron_mesh(cx, cy, cz, size):
    """Axis-aligned octahedron (two pyramids base-to-base) at (cx,cy,cz)."""
    s = size
    # 6 vertices: ±s along each axis
    vx = [cx+s, cx-s, cx,   cx,   cx,   cx  ]
    vy = [cy,   cy,   cy+s, cy-s, cy,   cy  ]
    vz = [cz,   cz,   cz,   cz,   cz+s, cz-s]
    # 8 faces
    ii = [0, 0, 0, 0, 1, 1, 1, 1]
    jj = [2, 4, 3, 5, 2, 5, 3, 4]
    kk = [4, 3, 5, 2, 4, 2, 5, 3]
    return vx, vy, vz, ii, jj, kk

