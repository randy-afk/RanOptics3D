"""Tests for the pure helper functions in ranoptics3d._plot (not the full
plot_optics_3d() pipeline — see test_integration.py for that)."""
import pytest

from ranoptics3d._plot import (
    _filter_by_range, _find_element_position, _parse_camera_eye,
    _build_annotations, compute_lattice_stats,
)


def _elems():
    return [
        {'name': 'QF1', 'key': 'quadrupole', 's_start': 0.0, 'length': 0.5},
        {'name': 'B1', 'key': 'sbend', 's_start': 0.5, 'length': 1.0},
        {'name': 'QF2', 'key': 'quadrupole', 's_start': 1.5, 'length': 0.5},
    ]


def _elems_with_floor():
    return [dict(e, flr_x0=i, flr_y0=0, flr_z0=0,
                  flr_x1=i + 1, flr_y1=0, flr_z1=0)
            for i, e in enumerate(_elems())]


# ─── _filter_by_range ─────────────────────────────────────────────────────────

def test_filter_by_range_numeric():
    names = [e['name'] for e in _filter_by_range(_elems(), '1.5:2.5')]
    assert names == ['B1', 'QF2']


def test_filter_by_range_swapped_bounds_still_works():
    names = [e['name'] for e in _filter_by_range(_elems(), '2.5:1.5')]
    assert names == ['B1', 'QF2']


def test_filter_by_range_by_element_name():
    # A dedicated fixture with a gap between elements, so the range
    # boundary doesn't overlap the excluded element (QF1 ends at 0.4,
    # well before B1 starts at 0.5 — avoids the inclusive `>=` boundary
    # ambiguity that _elems()'s back-to-back elements would create).
    gapped = [
        {'name': 'QF1', 'key': 'quadrupole', 's_start': 0.0, 'length': 0.4},
        {'name': 'B1', 'key': 'sbend', 's_start': 0.5, 'length': 1.0},
        {'name': 'QF2', 'key': 'quadrupole', 's_start': 1.5, 'length': 0.5},
    ]
    names = [e['name'] for e in _filter_by_range(gapped, 'B1:QF2')]
    assert names == ['B1', 'QF2']


def test_filter_by_range_none_returns_all():
    assert _filter_by_range(_elems(), None) == _elems()


def test_filter_by_range_unknown_element_raises():
    with pytest.raises(ValueError, match="not found"):
        _filter_by_range(_elems(), 'NOPE:QF2')


def test_filter_by_range_bad_format_raises():
    with pytest.raises(ValueError, match="Use START:END"):
        _filter_by_range(_elems(), 'a:b:c')


# ─── _find_element_position ──────────────────────────────────────────────────

def test_find_element_position_exact_match():
    pos = _find_element_position(_elems_with_floor(), 'QF1')
    assert pos == (0.5, 0.0, 0.0, 0.5)


def test_find_element_position_case_insensitive():
    pos = _find_element_position(_elems_with_floor(), 'qf1')
    assert pos is not None


def test_find_element_position_ambiguous_prefix_returns_none():
    # 'QF' matches both QF1 and QF2 as a prefix -> ambiguous -> None
    assert _find_element_position(_elems_with_floor(), 'QF') is None


def test_find_element_position_not_found_returns_none():
    assert _find_element_position(_elems_with_floor(), 'NOPE') is None


def test_find_element_position_empty_name_returns_none():
    assert _find_element_position(_elems_with_floor(), '') is None


# ─── _parse_camera_eye ────────────────────────────────────────────────────────

@pytest.mark.parametrize("spec", ["1.5,1.2,1.5", "1.5 1.2 1.5", " 1.5, 1.2, 1.5 "])
def test_parse_camera_eye_valid(spec):
    assert _parse_camera_eye(spec) == {'x': 1.5, 'y': 1.2, 'z': 1.5}


@pytest.mark.parametrize("spec", [None, "", "1.5,1.2", "a,b,c", "1,2,3,4"])
def test_parse_camera_eye_invalid_returns_none(spec):
    assert _parse_camera_eye(spec) is None


# ─── _build_annotations ───────────────────────────────────────────────────────

def test_build_annotations_matches_pattern():
    annots = _build_annotations(_elems_with_floor(), 'QF*')
    names = [a[3] for a in annots]
    assert names == ['QF1', 'QF2']


def test_build_annotations_empty_pattern_returns_empty():
    assert _build_annotations(_elems_with_floor(), '') == []
    assert _build_annotations(_elems_with_floor(), None) == []


def test_build_annotations_dedups_by_position():
    e = _elems_with_floor()[:1]
    dup = e + e  # same element twice -> same midpoint
    annots = _build_annotations(dup, 'QF*')
    assert len(annots) == 1


# ─── compute_lattice_stats ────────────────────────────────────────────────────

def test_compute_lattice_stats_counts_and_length():
    stats = compute_lattice_stats(_elems())
    assert stats['counts'] == {'Quadrupoles': 2, 'Dipoles': 1}
    assert stats['total_length'] == pytest.approx(2.0)
    assert stats['n_elements'] == 3
