"""Tests for ranoptics3d._elements — color/legend classification and hover text."""
from ranoptics3d._elements import (
    element_color, element_legend, make_hover, _normalize_key,
)


def test_normalize_key_aliases_elegant_truncated_names():
    assert _normalize_key('SOLE') == 'solenoid'
    assert _normalize_key('sben') == 'sbend'
    assert _normalize_key('Quad') == 'quadrupole'


def test_normalize_key_passthrough_for_unaliased():
    assert _normalize_key('quadrupole') == 'quadrupole'
    assert _normalize_key('  Sbend  ') == 'sbend'


def test_element_color_known_types():
    assert element_color('SBend') == '#d62728'
    assert element_color('quadrupole') == '#1f77b4'
    assert element_color('sole') == '#e377c2'  # aliased ELEGANT key


def test_element_color_unknown_returns_none():
    assert element_color('totally_unknown_type') is None


def test_element_legend_known_and_unknown():
    assert element_legend('QUAD') == 'Quadrupole'
    assert element_legend('drif') is None  # drift has no legend entry


def test_make_hover_quadrupole_shows_k1():
    elem = {'name': 'Q1', 'key': 'quadrupole', 'length': 0.5,
             's_start': 1.0, 'k1': 0.35}
    hover = make_hover(elem)
    assert 'K1 = 0.350000' in hover
    assert hover.endswith('<extra></extra>')


def test_make_hover_sbend_shows_angle_and_rho():
    elem = {'name': 'B1', 'key': 'sbend', 'length': 1.0, 's_start': 0.0,
             'angle': 0.1, 'raw_angle': 0.1, 'ref_tilt': 0.0}
    hover = make_hover(elem)
    assert 'Bend plane: Horizontal' in hover
    assert 'ρ' in hover


def test_make_hover_sbend_vertical_plane():
    import math
    elem = {'name': 'B1', 'key': 'sbend', 'length': 1.0, 's_start': 0.0,
             'angle': 0.1, 'raw_angle': 0.1, 'ref_tilt': math.pi / 2}
    hover = make_hover(elem)
    assert 'Bend plane: Vertical' in hover


def test_make_hover_rfcavity_voltage_and_frequency_thresholds():
    high = make_hover({'name': 'RF1', 'key': 'rfcavity', 'length': 1.0,
                        's_start': 0.0, 'voltage': 2e6, 'frequency': 1.3e9})
    assert 'V = 2.000 MV' in high
    assert 'f = 1.3000 GHz' in high

    low = make_hover({'name': 'RF2', 'key': 'rfcavity', 'length': 1.0,
                       's_start': 0.0, 'voltage': 500.0, 'frequency': 500e6})
    assert 'V = 500.0 V' in low
    assert 'f = 500.0000 MHz' in low


def test_make_hover_strips_bmad_lord_slash_prefix():
    elem = {'name': 'LORD\\Q1', 'key': 'quadrupole', 'length': 0.1,
             's_start': 0.0}
    hover = make_hover(elem)
    assert '<b>Q1</b>' in hover
