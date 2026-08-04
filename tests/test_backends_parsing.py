"""Tests for the pure text-parsing pieces of ranoptics3d._backends.

These deliberately avoid anything that shells out to an external binary
(elegant, madx) or needs pytao/xtrack installed — only the file-format
parsers and type-name mapping tables, which are plain Python.
"""
from ranoptics3d._backends.madx import _key_from_type_madx, _read_tfs
from ranoptics3d._backends.elegant import _key_from_type_elegant, _read_lte
from ranoptics3d._backends.xsuite import _key_from_type_xs
from ranoptics3d._backends.tao import _parse_tao_init


# ─── key/type mapping tables ─────────────────────────────────────────────────

def test_key_from_type_madx():
    assert _key_from_type_madx('SBEND') == 'sbend'
    assert _key_from_type_madx('QUADRUPOLE') == 'quadrupole'
    assert _key_from_type_madx('totally_unknown') == 'drift'


def test_key_from_type_elegant():
    assert _key_from_type_elegant('CSBEND') == 'SBend'
    assert _key_from_type_elegant('KQUAD') == 'Quadrupole'
    assert _key_from_type_elegant('weirdo') == 'Weirdo'  # falls back to capitalize()


def test_key_from_type_xsuite():
    assert _key_from_type_xs('Bend') == 'sbend'
    assert _key_from_type_xs('Multipole') == 'quadrupole'
    assert _key_from_type_xs('SomeCavity') == 'rfcavity'
    assert _key_from_type_xs('totally_unknown') == 'other'


# ─── MAD-X TFS parsing ────────────────────────────────────────────────────────

def test_read_tfs_parses_header_columns_and_quoted_names(tmp_path):
    p = tmp_path / "twiss.tfs"
    p.write_text(
        '@ NAME             %05s "TWISS"\n'
        '@ TYPE             %05s "TWISS"\n'
        '* NAME    KEYWORD     S      L     BETX\n'
        '$ %s      %s          %le    %le   %le\n'
        'QF1       QUADRUPOLE  0.5    0.5   10.0\n'
        'B1        SBEND       1.5    1.0   12.0\n'
        '"WEIRD NAME" MARKER   1.5    0.0   0.0\n'
    )
    scalars, cols, data = _read_tfs(str(p))
    assert scalars['NAME'] == 'TWISS'
    assert cols == ['NAME', 'KEYWORD', 'S', 'L', 'BETX']
    assert data['NAME'] == ['QF1', 'B1', 'WEIRD NAME']
    assert data['S'] == [0.5, 1.5, 1.5]
    assert data['BETX'] == [10.0, 12.0, 0.0]


# ─── ELEGANT .lte parsing ─────────────────────────────────────────────────────

def test_read_lte_parses_elements_with_params_and_comments(tmp_path):
    p = tmp_path / "lattice.lte"
    p.write_text(
        "! this is a comment\n"
        "QF1: KQUAD, L=0.5, K1=0.35\n"
        "B1: CSBEND, L=1.0, ANGLE=0.1 ! inline comment\n"
    )
    elems = _read_lte(str(p))
    assert elems['QF1']['type'] == 'KQUAD'
    assert elems['QF1']['K1'] == 0.35
    assert elems['B1']['type'] == 'CSBEND'
    assert elems['B1']['ANGLE'] == 0.1
    # Unset params default to 0.0
    assert elems['B1']['K1'] == 0.0


# ─── Tao .init parsing ────────────────────────────────────────────────────────

def test_parse_tao_init_multi_universe(tmp_path):
    p = tmp_path / "tao.init"
    p.write_text(
        "&tao_start\n"
        "  n_universes = 2\n"
        "/\n"
        "&tao_design_lattice\n"
        "  design_lattice(1)%file = 'ring1_lattice.bmad'\n"
        "  design_lattice(2)%file = 'ring2_lattice.bmad'\n"
        "/\n"
    )
    n, labels = _parse_tao_init(str(p))
    assert n == 2
    assert labels == {1: 'ring1', 2: 'ring2'}


def test_parse_tao_init_missing_file_defaults_to_single_universe():
    n, labels = _parse_tao_init('/nonexistent/tao.init')
    assert n == 1
    assert labels == {1: 'u1'}
