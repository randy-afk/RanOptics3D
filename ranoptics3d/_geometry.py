"""
ranoptics3d._geometry
=====================
3D mesh geometry builders for element boxes, bends, cavities,
edge outlines, and marker octahedra.
"""
from __future__ import annotations
import numpy as np

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


def _cross_mesh(x0, y0, z0, theta, phi, length, half_w, half_h, arm_frac=0.4):
    """Plus/cross shaped mesh for quadrupoles.

    Two overlapping boxes along the beam axis:
      - horizontal bar: full width (half_w), reduced height (half_h * arm_frac)
      - vertical bar:   reduced width (half_w * arm_frac), full height (half_h)

    arm_frac controls the thickness of each arm (0.4 = 40% of half dimension).
    """
    hw_thin = half_w * arm_frac
    hh_thin = half_h * arm_frac

    xs1, ys1, zs1, i1, j1, k1 = _box_mesh(
        x0, y0, z0, theta, phi, length, half_w, hh_thin)   # horizontal bar
    xs2, ys2, zs2, i2, j2, k2 = _box_mesh(
        x0, y0, z0, theta, phi, length, hw_thin, half_h)   # vertical bar

    offset = len(xs1)
    xs = xs1 + xs2
    ys = ys1 + ys2
    zs = zs1 + zs2
    ii = i1 + [v + offset for v in i2]
    jj = j1 + [v + offset for v in j2]
    kk = k1 + [v + offset for v in k2]
    return xs, ys, zs, ii, jj, kk



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


# ─── Solenoid helix mesh ──────────────────────────────────────────────────────

def _helix_mesh(x0, y0, z0, theta, phi, length,
                coil_r=0.12, tube_r=0.025,
                turns_per_m=4.0, n_coil=24, n_tube=8):
    """Helical coil mesh for solenoid rendering.

    The helix axis runs along the beam (forward) direction from (x0,y0,z0).
    The coil wraps around the beam axis with radius `coil_r`, making
    `turns_per_m * length` full turns. Each cross-section is a circle of
    radius `tube_r` (the wire thickness).

    Returns (vx, vy, vz, ii, jj, kk) for a Mesh3d trace.
    """
    right, up, fwd = _rot_matrix(theta, phi)
    right = np.array(right); up = np.array(up); fwd = np.array(fwd)
    origin = np.array([x0, y0, z0])

    n_turns = max(1.0, turns_per_m * length)
    n_spine = int(n_coil * n_turns)  # spine points along helix

    # Helix spine in local frame, then rotate to world frame
    t_vals = np.linspace(0, 2 * np.pi * n_turns, n_spine, endpoint=False)
    s_vals = np.linspace(0, length, n_spine, endpoint=False)

    spine = np.array([
        origin + s * fwd + coil_r * (np.cos(t) * right + np.sin(t) * up)
        for s, t in zip(s_vals, t_vals)
    ])  # shape (n_spine, 3)

    # Tube cross-sections: circle of radius tube_r around each spine point
    vx, vy, vz = [], [], []
    tube_angles = np.linspace(0, 2 * np.pi, n_tube, endpoint=False)

    for si in range(n_spine):
        # Local tangent at this spine point
        next_si = (si + 1) % n_spine
        tang = spine[next_si] - spine[si]
        norm = np.linalg.norm(tang)
        if norm < 1e-12:
            tang = fwd.copy()
        else:
            tang = tang / norm

        # Build two perpendicular axes to the tangent
        ref = up if abs(np.dot(tang, up)) < 0.9 else right
        perp1 = np.cross(tang, ref)
        n1 = np.linalg.norm(perp1)
        if n1 < 1e-12:
            perp1 = right.copy()
        else:
            perp1 = perp1 / n1
        perp2 = np.cross(tang, perp1)
        perp2 = perp2 / (np.linalg.norm(perp2) + 1e-12)

        for ta in tube_angles:
            pt = spine[si] + tube_r * (np.cos(ta) * perp1 + np.sin(ta) * perp2)
            vx.append(float(pt[0]))
            vy.append(float(pt[1]))
            vz.append(float(pt[2]))

    # Faces: quads between adjacent rings, each split into 2 triangles
    ii, jj, kk = [], [], []
    for si in range(n_spine):
        next_si = (si + 1) % n_spine
        for ti in range(n_tube):
            next_ti = (ti + 1) % n_tube
            a = si      * n_tube + ti
            b = si      * n_tube + next_ti
            c = next_si * n_tube + ti
            d = next_si * n_tube + next_ti
            ii += [a, a]; jj += [b, c]; kk += [c, d]

    return vx, vy, vz, ii, jj, kk


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


# ─── Aperture meshes ──────────────────────────────────────────────────────────

def _ellipse_edges(x0, y0, z0, theta, phi, length, radius_x, radius_y, n_sides=24):
    """Outline edges for an elliptical cylinder — two end rings + 4 longitudinal lines."""
    right, up, fwd = _rot_matrix(theta, phi)
    right  = np.array(right); up = np.array(up); fwd = np.array(fwd)
    origin = np.array([x0, y0, z0])
    end    = origin + fwd * length

    angles = np.linspace(0, 2 * np.pi, n_sides, endpoint=False)
    xs, ys, zs = [], [], []

    # Entry ring
    for a in angles:
        p = origin + radius_x * np.cos(a) * right + radius_y * np.sin(a) * up
        xs.append(float(p[0])); ys.append(float(p[1])); zs.append(float(p[2]))
    # Close entry ring
    p = origin + radius_x * right
    xs.append(float(p[0])); ys.append(float(p[1])); zs.append(float(p[2]))
    xs.append(None); ys.append(None); zs.append(None)

    # Exit ring
    for a in angles:
        p = end + radius_x * np.cos(a) * right + radius_y * np.sin(a) * up
        xs.append(float(p[0])); ys.append(float(p[1])); zs.append(float(p[2]))
    # Close exit ring
    p = end + radius_x * right
    xs.append(float(p[0])); ys.append(float(p[1])); zs.append(float(p[2]))
    xs.append(None); ys.append(None); zs.append(None)

    # 4 longitudinal lines at top, bottom, left, right
    for a in (0, np.pi/2, np.pi, 3*np.pi/2):
        pa = origin + radius_x * np.cos(a) * right + radius_y * np.sin(a) * up
        pb = end    + radius_x * np.cos(a) * right + radius_y * np.sin(a) * up
        xs += [float(pa[0]), float(pb[0]), None]
        ys += [float(pa[1]), float(pb[1]), None]
        zs += [float(pa[2]), float(pb[2]), None]

    return xs, ys, zs


def _aperture_cylinder_mesh(x0, y0, z0, theta, phi, length,
                             radius, radius_y=None, n_sides=24, caps=True):
    """Cylindrical or elliptical tube mesh for magnet body rendering.

    radius   — semi-axis in the right direction (x)
    radius_y — semi-axis in the up direction (y), defaults to radius (circle)
    """
    right, up, fwd = _rot_matrix(theta, phi)
    right  = np.array(right)
    up     = np.array(up)
    fwd    = np.array(fwd)
    origin = np.array([x0, y0, z0])
    end    = origin + fwd * length
    ry     = radius_y if radius_y is not None else radius

    angles = np.linspace(0, 2 * np.pi, n_sides, endpoint=False)
    vx, vy, vz = [], [], []

    # Entry ring (indices 0..n_sides-1), exit ring (indices n_sides..2*n_sides-1)
    for pt in (origin, end):
        for a in angles:
            p = pt + radius * np.cos(a) * right + ry * np.sin(a) * up
            vx.append(float(p[0]))
            vy.append(float(p[1]))
            vz.append(float(p[2]))

    # Side faces — two triangles per quad strip segment
    ii, jj, kk = [], [], []
    for si in range(n_sides):
        sn = (si + 1) % n_sides
        a  = si;          b  = sn
        c  = si + n_sides; d = sn + n_sides
        # Triangle 1: a, b, c  Triangle 2: b, d, c
        ii += [a, b]; jj += [b, d]; kk += [c, c]

    if caps:
        # Entry cap — center vertex fans to ring
        ec = len(vx)
        p = origin
        vx.append(float(p[0])); vy.append(float(p[1])); vz.append(float(p[2]))
        for si in range(n_sides):
            sn = (si + 1) % n_sides
            ii.append(ec); jj.append(si); kk.append(sn)
        # Exit cap
        xc = len(vx)
        p = end
        vx.append(float(p[0])); vy.append(float(p[1])); vz.append(float(p[2]))
        for si in range(n_sides):
            sn = (si + 1) % n_sides
            ii.append(xc); jj.append(sn + n_sides); kk.append(si + n_sides)

    return vx, vy, vz, ii, jj, kk


def _aperture_block_mesh(x0, y0, z0, theta, phi, length, half_x, half_y):
    """Box aperture mesh — same as _box_mesh but kept separate for clarity."""
    return _box_mesh(x0, y0, z0, theta, phi, length, half_x, half_y)


