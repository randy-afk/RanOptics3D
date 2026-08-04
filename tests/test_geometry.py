"""Tests for ranoptics3d._geometry — pure mesh-building math, no Plotly/Qt."""
import numpy as np
import pytest

from ranoptics3d._geometry import (
    _rot_matrix, _box_mesh, _bend_box_mesh, _ellipsoid_mesh, _box_edges,
    _octahedron_mesh, _helix_mesh, _ellipse_edges,
    _aperture_cylinder_mesh, _aperture_block_mesh,
    _offset_box_mesh, _quad_prism_mesh, _quad_prism_edges,
    _curved_bracket_mesh, _curved_bracket_edges,
    _multi_pole_mesh, _multi_pole_edges,
    _dipole_yoke_mesh, _dipole_yoke_edges, _bend_yoke_mesh,
)


def test_rot_matrix_identity_orientation():
    right, up, fwd = _rot_matrix(0.0, 0.0)
    np.testing.assert_allclose(right, [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(up, [0, 1, 0], atol=1e-12)
    np.testing.assert_allclose(fwd, [0, 0, 1], atol=1e-12)


@pytest.mark.parametrize("theta,phi", [
    (0.0, 0.0), (0.3, 0.0), (0.0, 0.5), (1.2, -0.4), (-2.1, 0.9),
])
def test_rot_matrix_orthonormal(theta, phi):
    right, up, fwd = _rot_matrix(theta, phi)
    for v in (right, up, fwd):
        assert np.linalg.norm(v) == pytest.approx(1.0, abs=1e-10)
    assert np.dot(right, up) == pytest.approx(0.0, abs=1e-10)
    assert np.dot(right, fwd) == pytest.approx(0.0, abs=1e-10)
    assert np.dot(up, fwd) == pytest.approx(0.0, abs=1e-10)


def test_box_mesh_vertex_and_face_counts():
    xs, ys, zs, i, j, k = _box_mesh(0, 0, 0, 0.0, 0.0, 2.0, 1.0, 0.5)
    assert len(xs) == len(ys) == len(zs) == 8
    assert len(i) == len(j) == len(k) == 12  # 12 triangles for a box


def test_box_mesh_extents_at_identity_orientation():
    xs, ys, zs, *_ = _box_mesh(0, 0, 0, 0.0, 0.0, 2.0, 1.0, 0.5)
    assert min(xs) == pytest.approx(-1.0) and max(xs) == pytest.approx(1.0)
    assert min(ys) == pytest.approx(-0.5) and max(ys) == pytest.approx(0.5)
    assert min(zs) == pytest.approx(0.0) and max(zs) == pytest.approx(2.0)


def test_bend_box_mesh_zero_angle_matches_box_mesh():
    straight = _box_mesh(0, 0, 0, 0.1, 0.2, 2.0, 1.0, 0.5)
    bend = _bend_box_mesh(0, 0, 0, 0.1, 0.2, 2.0, 0.0, 1.0, 0.5, n_seg=7)
    assert len(bend[0]) == len(straight[0])


def test_bend_box_mesh_segments_multiply_vertex_count():
    single = _box_mesh(0, 0, 0, 0.0, 0.0, 0.4, 1.0, 0.5)
    n_seg = 5
    bend = _bend_box_mesh(0, 0, 0, 0.0, 0.0, 2.0, 0.3, 1.0, 0.5, n_seg=n_seg)
    assert len(bend[0]) == n_seg * len(single[0])
    assert len(bend[3]) == n_seg * len(single[3])  # face index arrays too


def test_ellipsoid_mesh_vertex_count():
    n_lat, n_lon = 8, 12
    xs, ys, zs, ii, jj, kk = _ellipsoid_mesh(
        0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2, n_lat=n_lat, n_lon=n_lon)
    assert len(xs) == (n_lat + 1) * n_lon


def test_box_edges_length():
    xs, ys, zs = _box_edges(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2)
    # 12 edges, 3 entries each (start, end, None separator)
    assert len(xs) == len(ys) == len(zs) == 36


def test_octahedron_mesh_shape():
    size = 0.1
    vx, vy, vz, ii, jj, kk = _octahedron_mesh(1.0, 2.0, 3.0, size)
    assert len(vx) == 6
    assert len(ii) == len(jj) == len(kk) == 8
    # Vertices are size away from center along each axis
    assert max(vx) - 1.0 == pytest.approx(size)
    assert min(vx) - 1.0 == pytest.approx(-size)


def test_helix_mesh_radius_bounds():
    coil_r, tube_r = 0.12, 0.025
    vx, vy, vz, ii, jj, kk = _helix_mesh(
        0, 0, 0, 0.0, 0.0, 1.0, coil_r=coil_r, tube_r=tube_r,
        turns_per_m=4.0, n_coil=24, n_tube=8)
    assert len(vx) > 0
    # At theta=phi=0, fwd=z, so radial distance from the beam axis in x-y
    # should stay within [coil_r - tube_r, coil_r + tube_r].
    d = np.hypot(np.array(vx), np.array(vy))
    assert d.min() >= coil_r - tube_r - 1e-9
    assert d.max() <= coil_r + tube_r + 1e-9


def test_ellipse_edges_nonempty():
    xs, ys, zs = _ellipse_edges(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.1, n_sides=8)
    assert len(xs) == len(ys) == len(zs)
    assert len(xs) > 0


def test_aperture_cylinder_mesh_caps_add_vertices_and_faces():
    n_sides = 8
    with_caps = _aperture_cylinder_mesh(
        0, 0, 0, 0.0, 0.0, 1.0, radius=0.2, radius_y=0.1,
        n_sides=n_sides, caps=True)
    no_caps = _aperture_cylinder_mesh(
        0, 0, 0, 0.0, 0.0, 1.0, radius=0.2, radius_y=0.1,
        n_sides=n_sides, caps=False)
    assert len(with_caps[0]) == 2 * n_sides + 2
    assert len(no_caps[0]) == 2 * n_sides
    assert len(with_caps[3]) > len(no_caps[3])  # more triangles with caps


def test_aperture_block_mesh_is_box_mesh():
    a = _aperture_block_mesh(0, 0, 0, 0.0, 0.0, 1.0, 0.3, 0.2)
    b = _box_mesh(0, 0, 0, 0.0, 0.0, 1.0, 0.3, 0.2)
    assert a == b


def test_aperture_cylinder_mesh_cap_normals_point_outward():
    """Regression test for a real, pre-existing bug found while verifying
    the multi-pole bore geometry: the entry/exit cap fan triangles had
    inverted winding — normals pointed into the tube instead of away
    from it (entry cap pointed +fwd instead of -fwd, and vice versa for
    the exit cap). This didn't crash anything, but would shade the flat
    caps incorrectly. Fixed by swapping the fan winding order."""
    x0, y0, z0 = 0.0, 0.0, 0.0
    theta, phi, length = 0.3, -0.2, 1.0
    n_sides = 16
    right, up, fwd = _rot_matrix(theta, phi)
    fwd = np.array(fwd)
    origin = np.array([x0, y0, z0])

    xs, ys, zs, i, j, k = _aperture_cylinder_mesh(
        x0, y0, z0, theta, phi, length, radius=0.1, radius_y=0.08,
        n_sides=n_sides, caps=True)
    verts = np.array(list(zip(xs, ys, zs)))

    n_side_faces = 2 * n_sides
    for idx in range(n_side_faces, len(i)):
        a, b, c = i[idx], j[idx], k[idx]
        t0, t1, t2 = verts[a], verts[b], verts[c]
        normal = np.cross(t1 - t0, t2 - t0)
        face_center = (t0 + t1 + t2) / 3
        proj = np.dot(face_center - origin, fwd)
        expected_dir = -fwd if proj < length / 2 else fwd
        assert np.dot(normal, expected_dir) > 0, \
            f"cap face {idx} normal points into the tube, not away from it"


# ─── Realistic magnet shapes ──────────────────────────────────────────────────
#
# These shapes are composed entirely from repeated _box_mesh calls (via
# _offset_box_mesh), so every mesh is a sequence of 8-vertex/12-face box
# "chunks". The helpers below verify index bounds, non-degenerate triangles,
# and outward-facing normals per chunk — directly guarding against the
# "glitchy geometry" (inverted faces / self-intersecting triangles) failure
# mode that a prior, unrelated attempt at this feature reportedly hit.

def _assert_indices_in_bounds(xs, i, j, k):
    n = len(xs)
    all_idx = list(i) + list(j) + list(k)
    assert all_idx, "mesh has no faces"
    assert min(all_idx) >= 0
    assert max(all_idx) < n


def _assert_no_degenerate_triangles(xs, ys, zs, i, j, k, atol=1e-12):
    verts = np.array(list(zip(xs, ys, zs)))
    for a, b, c in zip(i, j, k):
        v0, v1, v2 = verts[a], verts[b], verts[c]
        area = np.linalg.norm(np.cross(v1 - v0, v2 - v0)) / 2
        assert area > atol, f"degenerate triangle at indices ({a},{b},{c})"


def _assert_outward_normals_per_box_chunk(xs, ys, zs, i, j, k):
    """Every one of these shapes is a concatenation of plain 8-vertex/
    12-face boxes. For each box chunk, confirm each face's outward normal
    points away from that box's own centroid — the direct check against
    inverted-face geometry."""
    verts = np.array(list(zip(xs, ys, zs)))
    n_boxes = len(xs) // 8
    assert len(xs) % 8 == 0, "expected a whole number of 8-vertex box chunks"
    assert len(i) % 12 == 0, "expected a whole number of 12-face box chunks"
    for b in range(n_boxes):
        v0, v1 = b * 8, (b + 1) * 8
        centroid = verts[v0:v1].mean(axis=0)
        f0, f1 = b * 12, (b + 1) * 12
        for fi in range(f0, f1):
            a, bb, c = i[fi], j[fi], k[fi]
            t0, t1, t2 = verts[a], verts[bb], verts[c]
            normal = np.cross(t1 - t0, t2 - t0)
            face_center = (t0 + t1 + t2) / 3
            outward = face_center - centroid
            dot = np.dot(normal, outward)
            assert dot > 0, f"inverted face in box chunk {b}, face {fi}"


def _assert_mesh_integrity(mesh):
    # mesh may be a plain 6-tuple (xs,ys,zs,i,j,k) or a 7-tuple that also
    # carries a face_tags list (body/coil) — ignore the tags here, they're
    # checked separately where relevant.
    xs, ys, zs, i, j, k = mesh[:6]
    _assert_indices_in_bounds(xs, i, j, k)
    _assert_no_degenerate_triangles(xs, ys, zs, i, j, k)
    _assert_outward_normals_per_box_chunk(xs, ys, zs, i, j, k)


def _assert_mixed_chunk_integrity(mesh, chunk_sizes):
    """Like _assert_mesh_integrity, but for composites of differently
    sized sub-shapes (chunk_sizes: [(n_verts, n_faces), ...] in order —
    e.g. a flat plate + a cylindrical bore + several curved-bracket
    segments). Bounds and non-degeneracy are checked for every triangle;
    the outward-normal check applies to 8-vertex/12-face quad-prism
    chunks (boxes, bracket segments — where "points away from the
    chunk's own centroid" is a valid outward test) and is skipped for
    other chunk shapes such as a capped cylinder, where a single flat
    centroid isn't a meaningful reference for both the curved wall and
    the flat end caps.
    """
    xs, ys, zs, i, j, k = mesh[:6]
    verts = np.array(list(zip(xs, ys, zs)))
    _assert_indices_in_bounds(xs, i, j, k)
    _assert_no_degenerate_triangles(xs, ys, zs, i, j, k)

    v_off, f_off = 0, 0
    for n_v, n_f in chunk_sizes:
        if (n_v, n_f) == (8, 12):
            centroid = verts[v_off:v_off + n_v].mean(axis=0)
            for fi in range(f_off, f_off + n_f):
                a, b, c = i[fi], j[fi], k[fi]
                t0, t1, t2 = verts[a], verts[b], verts[c]
                normal = np.cross(t1 - t0, t2 - t0)
                face_center = (t0 + t1 + t2) / 3
                assert np.dot(normal, face_center - centroid) > 0, \
                    f"inverted face at vertex offset {v_off}, face {fi}"
        v_off += n_v
        f_off += n_f
    assert v_off == len(xs), "chunk_sizes don't account for all vertices"
    assert f_off == len(i), "chunk_sizes don't account for all faces"


# ─── _offset_box_mesh ─────────────────────────────────────────────────────────

def test_offset_box_mesh_zero_offset_equals_box_mesh():
    a = _box_mesh(0, 0, 0, 0.2, 0.1, 1.0, 0.3, 0.2)
    b = _offset_box_mesh(0, 0, 0, 0.2, 0.1, 1.0, 0.3, 0.2,
                         offset_u=0.0, offset_v=0.0)
    assert a == b


def test_offset_box_mesh_shifts_bounding_box_center():
    right, up, _ = _rot_matrix(0.0, 0.0)
    xs, ys, zs, *_ = _offset_box_mesh(0, 0, 0, 0.0, 0.0, 1.0, 0.1, 0.1,
                                      offset_u=0.5, offset_v=0.3)
    verts = np.array(list(zip(xs, ys, zs)))
    center = verts.mean(axis=0)
    expected = np.array(right) * 0.5 + np.array(up) * 0.3 + np.array([0, 0, 0.5])
    np.testing.assert_allclose(center, expected, atol=1e-9)


# ─── _quad_prism_mesh ──────────────────────────────────────────────────────────

def test_quad_prism_mesh_rectangle_matches_box_mesh():
    hw, hh = 0.3, 0.2
    rect = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    a = _box_mesh(0, 0, 0, 0.2, 0.1, 1.0, hw, hh)
    b = _quad_prism_mesh(0, 0, 0, 0.2, 0.1, 1.0, rect)
    for arr_a, arr_b in zip(a, b):
        np.testing.assert_allclose(arr_a, arr_b, atol=1e-12)


def test_quad_prism_mesh_trapezoid_integrity():
    # Narrow at one end, wide at the other — the tapered pole profile.
    trap = [(-0.05, -0.05), (0.05, -0.05), (0.15, 0.05), (-0.15, 0.05)]
    mesh = _quad_prism_mesh(0, 0, 0, 0.4, -0.1, 1.0, trap)
    _assert_mesh_integrity(mesh)


def test_quad_prism_edges_nonempty():
    hw, hh = 0.3, 0.2
    rect = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    xs, ys, zs = _quad_prism_edges(0, 0, 0, 0.0, 0.0, 1.0, rect)
    assert len(xs) == len(ys) == len(zs) == 36  # same as _box_edges


# ─── _curved_bracket_mesh ──────────────────────────────────────────────────────

@pytest.mark.parametrize("n_seg", [4, 8, 12])
def test_curved_bracket_mesh_vertex_and_face_counts(n_seg):
    mesh = _curved_bracket_mesh(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2,
                                start_angle=-0.5, end_angle=0.5,
                                inner_radius_frac=0.24, outer_radius_frac=0.62,
                                n_seg=n_seg)
    xs, ys, zs, i, j, k = mesh
    assert len(xs) == 8 * n_seg
    assert len(i) == 12 * n_seg


def test_curved_bracket_mesh_integrity_small_and_wide_arcs():
    small = _curved_bracket_mesh(0, 0, 0, 0.3, -0.2, 1.0, 0.2, 0.2,
                                 -0.5, 0.5, 0.24, 0.62, n_seg=8)
    _assert_mesh_integrity(small)
    wide = _curved_bracket_mesh(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.15,
                                0.1, 2.0, 0.3, 0.7, n_seg=12)
    _assert_mesh_integrity(wide)


def test_curved_bracket_edges_nonempty():
    xs, ys, zs = _curved_bracket_edges(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2,
                                       -0.5, 0.5, 0.24, 0.62, n_seg=8)
    assert len(xs) == len(ys) == len(zs)
    assert len(xs) > 0


# ─── _multi_pole_mesh (quad/sext/octupole) ────────────────────────────────────
#
# Composite: a flat backing plate (8v/12f box) + a central bore
# (_aperture_cylinder_mesh, n_sides=16 caps=True -> 2*16+2=34 verts,
# 2*16 side + 2*16 cap = 64 faces) + n_poles curved brackets (n_seg
# segments each, 8v/12f per segment).

def _expected_multi_pole_chunks(n_poles, n_seg=8, n_sides=16):
    chunks = [(8, 12), (2 * n_sides + 2, 4 * n_sides)]
    chunks += [(8, 12)] * (n_poles * n_seg)
    return chunks


@pytest.mark.parametrize("n_poles", [4, 6, 8])
def test_multi_pole_mesh_vertex_and_face_counts(n_poles):
    mesh = _multi_pole_mesh(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2, n_poles=n_poles)
    xs, ys, zs, i, j, k, face_tags = mesh
    chunks = _expected_multi_pole_chunks(n_poles)
    assert len(xs) == sum(v for v, f in chunks)
    assert len(i) == sum(f for v, f in chunks)
    assert len(face_tags) == len(i)
    assert set(face_tags) == {'body', 'coil'}


@pytest.mark.parametrize("n_poles", [4, 6, 8])
def test_multi_pole_mesh_integrity(n_poles):
    mesh = _multi_pole_mesh(0, 0, 0, 0.3, -0.2, 1.0, 0.2, 0.2, n_poles=n_poles)
    _assert_mixed_chunk_integrity(mesh, _expected_multi_pole_chunks(n_poles))


def test_multi_pole_edges_nonempty():
    xs, ys, zs = _multi_pole_edges(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2, n_poles=4)
    assert len(xs) == len(ys) == len(zs)
    assert len(xs) > 0


# ─── _dipole_yoke_mesh ─────────────────────────────────────────────────────────

def test_dipole_yoke_mesh_vertex_and_face_counts():
    mesh = _dipole_yoke_mesh(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2)
    xs, ys, zs, i, j, k, face_tags = mesh
    # top/bottom pole slabs + left/right return-yoke bars + top/bottom
    # coil accent strips = 6 boxes
    assert len(xs) == 48
    assert len(i) == 72
    assert len(face_tags) == len(i)
    assert set(face_tags) == {'body', 'coil'}


def test_dipole_yoke_mesh_integrity():
    mesh = _dipole_yoke_mesh(0, 0, 0, 0.4, 0.1, 1.0, 0.2, 0.2)
    _assert_mesh_integrity(mesh)


def test_dipole_yoke_mesh_has_visible_gap():
    """The top and bottom pole slabs must not overlap — there should be a
    gap for the beam channel between them."""
    xs, ys, zs, i, j, k, face_tags = _dipole_yoke_mesh(
        0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2, gap_frac=0.3)
    ys = np.array(ys)
    top_ys = ys[ys > 0]
    bottom_ys = ys[ys < 0]
    assert top_ys.min() > 0  # gap: nothing crosses y=0
    assert bottom_ys.max() < 0
    assert top_ys.min() == pytest.approx(0.2 * 0.3, abs=1e-9)


def test_dipole_yoke_edges_nonempty():
    xs, ys, zs = _dipole_yoke_edges(0, 0, 0, 0.0, 0.0, 1.0, 0.2, 0.2)
    assert len(xs) == len(ys) == len(zs)
    assert len(xs) > 0


# ─── _bend_yoke_mesh ───────────────────────────────────────────────────────────

def test_bend_yoke_mesh_zero_angle_matches_dipole_yoke_mesh():
    straight = _dipole_yoke_mesh(0, 0, 0, 0.1, 0.2, 2.0, 0.2, 0.2)
    bend = _bend_yoke_mesh(0, 0, 0, 0.1, 0.2, 2.0, 0.0, 0.2, 0.2, n_seg=7)
    assert len(bend[0]) == len(straight[0])


def test_bend_yoke_mesh_segments_multiply_vertex_count():
    single = _dipole_yoke_mesh(0, 0, 0, 0.0, 0.0, 0.4, 0.2, 0.2)
    n_seg = 5
    bend = _bend_yoke_mesh(0, 0, 0, 0.0, 0.0, 2.0, 0.3, 0.2, 0.2, n_seg=n_seg)
    assert len(bend[0]) == n_seg * len(single[0])
    assert len(bend[3]) == n_seg * len(single[3])


@pytest.mark.parametrize("vertical", [False, True])
def test_bend_yoke_mesh_integrity(vertical):
    mesh = _bend_yoke_mesh(0, 0, 0, 0.0, 0.0, 2.0, 0.3, 0.2, 0.2,
                           n_seg=8, vertical=vertical)
    _assert_mesh_integrity(mesh)
