"""Tests for ranoptics3d._mesh — trace/mesh assembly and the tunnel-wall reader.

The tunnel-wall tests are a direct regression check for a bug fixed this
session: _read_tunnel_wall used re.split() without `import re`, so every
call silently failed (caught by a broad except) and the tunnel-wall
feature never rendered anything.
"""
from ranoptics3d._mesh import (
    _read_tunnel_wall, _build_beampipe_trace, _build_element_meshes,
    _build_twiss_tube, _build_crosshair_lines, _COIL_COLOR,
)


def _elem(name, key, s_start, length, **extra):
    e = {'name': name, 'key': key, 's_start': s_start, 'length': length}
    e.update(extra)
    return e


def _synthetic_lattice():
    return [
        _elem('QF1', 'quadrupole', 0.0, 0.5, k1=0.3,
              flr_x0=0, flr_y0=0, flr_z0=0.0,
              flr_x1=0, flr_y1=0, flr_z1=0.5,
              flr_theta0=0.0, flr_phi0=0.0),
        _elem('B1', 'sbend', 0.5, 1.0, angle=0.1, raw_angle=0.1, ref_tilt=0.0,
              flr_x0=0, flr_y0=0, flr_z0=0.5,
              flr_x1=0.05, flr_y1=0, flr_z1=1.5,
              flr_theta0=0.0, flr_phi0=0.0),
        _elem('RF1', 'rfcavity', 1.5, 0.3,
              flr_x0=0.05, flr_y0=0, flr_z0=1.5,
              flr_x1=0.05, flr_y1=0, flr_z1=1.8,
              flr_theta0=0.0, flr_phi0=0.0),
        _elem('SOLE1', 'solenoid', 1.8, 0.2,
              flr_x0=0.05, flr_y0=0, flr_z0=1.8,
              flr_x1=0.05, flr_y1=0, flr_z1=2.0,
              flr_theta0=0.0, flr_phi0=0.0),
        _elem('BPM1', 'monitor', 2.0, 0.0,
              flr_x0=0.05, flr_y0=0, flr_z0=2.0,
              flr_x1=0.05, flr_y1=0, flr_z1=2.0,
              flr_theta0=0.0, flr_phi0=0.0),
    ]


# ─── _read_tunnel_wall regression tests ──────────────────────────────────────

def test_read_tunnel_wall_open_path(tmp_path):
    p = tmp_path / "tunnel.dat"
    p.write_text("0 0 0 1 1 1\n1 1 1 2 2 2\n2 2 2 3 3 3\n")
    result = _read_tunnel_wall(str(p))
    assert result is not None
    assert not result['is_ring']  # numpy bool_, so avoid `is False`
    assert len(result['xi']) == 3


def test_read_tunnel_wall_closed_ring(tmp_path):
    p = tmp_path / "tunnel.dat"
    p.write_text("0 0 0 1 1 1\n1 1 1 2 2 2\n0 0 0.0001 1 1 1\n")
    result = _read_tunnel_wall(str(p))
    assert result is not None
    assert result['is_ring']  # numpy bool_, so avoid `is True`
    assert len(result['xi']) == 4  # closing point appended


def test_read_tunnel_wall_malformed_returns_none_without_raising(tmp_path):
    p = tmp_path / "tunnel.dat"
    p.write_text("this is not tunnel data\n")
    assert _read_tunnel_wall(str(p)) is None


def test_read_tunnel_wall_missing_file_returns_none():
    assert _read_tunnel_wall("/nonexistent/path/tunnel.dat") is None


def test_read_tunnel_wall_logs_no_python_errors(tmp_path):
    """The reader must not report an internal NameError/ImportError via log_fn
    for well-formed input — that's exactly how the missing `import re` bug
    manifested (silently, only visible in the log)."""
    p = tmp_path / "tunnel.dat"
    p.write_text("0 0 0 1 1 1\n1 1 1 2 2 2\n")
    messages = []
    result = _read_tunnel_wall(str(p), log_fn=messages.append)
    assert result is not None
    assert not any('not defined' in m for m in messages)


# ─── _build_element_meshes ────────────────────────────────────────────────────

def test_build_element_meshes_groups_by_legend_name():
    groups, outlines, markers = _build_element_meshes(
        _synthetic_lattice(), show_markers=False)
    assert set(groups.keys()) == {'Quadrupole', 'Dipole', 'RF Cavity', 'Solenoid'}
    assert markers['xs'] == []  # monitor excluded when show_markers=False


def test_build_element_meshes_includes_markers_when_requested():
    groups, outlines, markers = _build_element_meshes(
        _synthetic_lattice(), show_markers=True)
    assert len(markers['xs']) > 0


def test_build_element_meshes_cylinder_shape_override():
    elem = _elem('MQA1', 'quadrupole', 0.0, 0.5, k1=0.3,
                  flr_x0=0, flr_y0=0, flr_z0=0.0,
                  flr_x1=0, flr_y1=0, flr_z1=0.5,
                  flr_theta0=0.0, flr_phi0=0.0,
                  _mag_hw=0.15, _mag_hh=0.15, _mag_shape='cylinder')
    groups, outlines, markers = _build_element_meshes([elem])
    assert 'Quadrupole' in groups
    assert len(groups['Quadrupole']['xs']) > 0


def test_build_element_meshes_realistic_magnets_off_matches_plain_boxes():
    """realistic_magnets=False (the default) must reproduce the exact
    original box-rendering vertex counts — the safety fallback the
    feature was built around."""
    lattice = _synthetic_lattice()
    groups, outlines, markers = _build_element_meshes(
        lattice, show_markers=False, realistic_magnets=False)
    # Quadrupole/RF Cavity/Solenoid are single elements -> single-shape
    # vertex counts (8 for a plain box quadrupole).
    assert len(groups['Quadrupole']['xs']) == 8


def _expected_multi_pole_verts(n_poles, n_seg=8, n_sides=16):
    """Plate (8v box) + bore (_aperture_cylinder_mesh, n_sides=16,
    caps=True -> 2*n_sides+2 verts) + n_poles curved brackets (n_seg
    quad-prism segments each, 8v per segment)."""
    return 8 + (2 * n_sides + 2) + n_poles * n_seg * 8


def test_build_element_meshes_realistic_magnets_on_uses_new_shapes():
    lattice = _synthetic_lattice()
    groups, outlines, markers = _build_element_meshes(
        lattice, show_markers=False, realistic_magnets=True)
    assert len(groups['Quadrupole']['xs']) == _expected_multi_pole_verts(4)
    # Dipole (angle=0.1, segmented) = bend_segments(12) * yoke(48 verts:
    # top/bottom/left/right bars + top/bottom coil accents = 6 boxes)
    assert len(groups['Dipole']['xs']) == 12 * 48
    for legend_name, g in groups.items():
        all_idx = g['i'] + g['j'] + g['k']
        assert max(all_idx) < len(g['xs'])
        assert len(g['hover']) == len(g['xs'])


def test_build_element_meshes_realistic_magnets_sextupole_octupole():
    lattice = [
        _elem('SF1', 'sextupole', 0.0, 0.3,
              flr_x0=0, flr_y0=0, flr_z0=0.0,
              flr_x1=0, flr_y1=0, flr_z1=0.3,
              flr_theta0=0.0, flr_phi0=0.0),
        _elem('OCT1', 'octupole', 0.3, 0.3,
              flr_x0=0, flr_y0=0, flr_z0=0.3,
              flr_x1=0, flr_y1=0, flr_z1=0.6,
              flr_theta0=0.0, flr_phi0=0.0),
    ]
    groups, outlines, markers = _build_element_meshes(
        lattice, realistic_magnets=True)
    assert len(groups['Sextupole']['xs']) == _expected_multi_pole_verts(6)
    assert len(groups['Octupole']['xs']) == _expected_multi_pole_verts(8)


def test_build_element_meshes_realistic_magnets_facecolor_contrasts_coils():
    """The coil/pole-piece faces must be colored differently from the
    body/yoke faces within the same trace — otherwise (as reported) the
    coil detail is invisible, blending into one solid color."""
    lattice = _synthetic_lattice()  # includes QF1 (quadrupole), B1 (sbend)
    groups, outlines, markers = _build_element_meshes(
        lattice, show_markers=False, realistic_magnets=True)

    quad = groups['Quadrupole']
    assert len(quad['facecolor']) == len(quad['i'])
    assert set(quad['facecolor']) == {quad['color'], _COIL_COLOR}

    dipole = groups['Dipole']
    assert len(dipole['facecolor']) == len(dipole['i'])
    assert set(dipole['facecolor']) == {dipole['color'], _COIL_COLOR}


def test_build_element_meshes_realistic_magnets_off_has_no_facecolor():
    lattice = _synthetic_lattice()
    groups, outlines, markers = _build_element_meshes(
        lattice, show_markers=False, realistic_magnets=False)
    for legend_name, g in groups.items():
        assert g['facecolor'] == []


def test_build_element_meshes_realistic_magnets_kicker_uses_dipole_shape():
    """Correctors (kicker/hkicker/vkicker) are physically small dipoles,
    so realistic mode should give them the dipole yoke shape, not a
    plain box."""
    lattice = [
        _elem('HK1', 'hkicker', 0.0, 0.2,
              flr_x0=0, flr_y0=0, flr_z0=0.0,
              flr_x1=0, flr_y1=0, flr_z1=0.2,
              flr_theta0=0.0, flr_phi0=0.0),
    ]
    groups, outlines, markers = _build_element_meshes(
        lattice, realistic_magnets=True)
    # Dipole yoke = 6 boxes * 8 verts = 48 (see _dipole_yoke_mesh)
    assert len(groups['Kicker']['xs']) == 48
    assert set(groups['Kicker']['facecolor']) == \
        {groups['Kicker']['color'], _COIL_COLOR}

    groups_off, _, _ = _build_element_meshes(lattice, realistic_magnets=False)
    assert len(groups_off['Kicker']['xs']) == 8  # plain box, unchanged


# ─── _build_beampipe_trace ────────────────────────────────────────────────────

def test_build_beampipe_trace_connects_entry_exit_points():
    trace = _build_beampipe_trace(_synthetic_lattice())
    assert trace is not None
    assert len(trace['x']) == 2 * len(_synthetic_lattice())


def test_build_beampipe_trace_none_without_floor_coords():
    elems = [_elem('D1', 'drift', 0.0, 1.0)]  # no flr_x0 etc.
    assert _build_beampipe_trace(elems) is None


# ─── Twiss tube / crosshairs ──────────────────────────────────────────────────

def test_build_twiss_tube_requires_beta_data():
    lattice = _synthetic_lattice()  # no beta_x/beta_y set
    assert _build_twiss_tube(lattice, 1e-9, 1e-9) is None


def test_build_twiss_tube_with_beta_data():
    lattice = [dict(e, beta_x=5.0, beta_y=3.0) for e in _synthetic_lattice()]
    tube = _build_twiss_tube(lattice, 1e-9, 1e-9, n_phi=8)
    assert tube is not None
    assert len(tube['xs']) == len(lattice) * 8


def test_build_crosshair_lines_pairs_match_element_count():
    lattice = [dict(e, beta_x=5.0, beta_y=3.0) for e in _synthetic_lattice()]
    ch_x, ch_y = _build_crosshair_lines(lattice, 1e-9, 1e-9)
    # 3 entries per element (start, end, None separator)
    assert len(ch_x['xs']) == 3 * len(lattice)
    assert len(ch_y['xs']) == 3 * len(lattice)
