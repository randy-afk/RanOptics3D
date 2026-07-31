"""Tests for ranoptics3d._geometry — pure mesh-building math, no Plotly/Qt."""
import numpy as np
import pytest

from ranoptics3d._geometry import (
    _rot_matrix, _box_mesh, _bend_box_mesh, _ellipsoid_mesh, _box_edges,
    _octahedron_mesh, _helix_mesh, _ellipse_edges,
    _aperture_cylinder_mesh, _aperture_block_mesh,
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
