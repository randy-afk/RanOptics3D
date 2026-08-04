"""Tests for ranoptics3d._aperture — magnet size file parsing and matching."""
from ranoptics3d._aperture import parse_aperture_file, match_apertures


def _write(tmp_path, content):
    p = tmp_path / "sizes.dat"
    p.write_text(content)
    return str(p)


def test_parse_aperture_file_full_and_defaulted_rows(tmp_path):
    path = _write(tmp_path, """
# comment line
MQA*        cylinder   10.0          10.0
MQB*        block      8.0           12.0
QF          block      8.0
QD
""")
    entries = parse_aperture_file(path)
    assert entries == [
        {'pattern': 'MQA*', 'shape': 'cylinder', 'outer_x': 10.0, 'outer_y': 10.0},
        {'pattern': 'MQB*', 'shape': 'block', 'outer_x': 8.0, 'outer_y': 12.0},
        {'pattern': 'QF', 'shape': 'block', 'outer_x': 8.0, 'outer_y': 8.0},
        {'pattern': 'QD', 'shape': 'block', 'outer_x': None, 'outer_y': None},
    ]


def test_parse_aperture_file_comma_separated(tmp_path):
    path = _write(tmp_path, "MQA*, cylinder, 5.0, 5.0\n")
    entries = parse_aperture_file(path)
    assert entries[0]['pattern'] == 'MQA*'
    assert entries[0]['shape'] == 'cylinder'
    assert entries[0]['outer_x'] == 5.0


def test_parse_aperture_file_outer_x_without_shape_keyword(tmp_path):
    # Second token isn't 'cylinder'/'block' -> treated as outer_x directly.
    path = _write(tmp_path, "QF 8.0 6.0\n")
    entries = parse_aperture_file(path)
    assert entries[0]['shape'] == 'block'
    assert entries[0]['outer_x'] == 8.0
    assert entries[0]['outer_y'] == 6.0


def test_match_apertures_wildcards_and_unit_conversion():
    entries = [
        {'pattern': 'MQA*', 'shape': 'cylinder', 'outer_x': 10.0, 'outer_y': 10.0},
        {'pattern': 'QD', 'shape': 'block', 'outer_x': None, 'outer_y': None},
    ]
    elements = [
        {'name': 'MQA01', 'length': 0.3},
        {'name': 'QD', 'length': 0.3},
        {'name': 'NOMATCH', 'length': 0.3},
    ]
    matched = match_apertures(elements, entries, default_hw=0.2)
    assert len(matched) == 2  # NOMATCH excluded — only explicitly matched elements returned

    mqa = next(m for m in matched if m['element']['name'] == 'MQA01')
    assert mqa['shape'] == 'cylinder'
    assert mqa['outer_x'] == 0.1  # 10 cm -> 0.1 m

    qd = next(m for m in matched if m['element']['name'] == 'QD')
    assert qd['outer_x'] == 0.2  # falls back to default_hw since unspecified


def test_match_apertures_first_pattern_wins():
    entries = [
        {'pattern': 'Q*', 'shape': 'block', 'outer_x': 1.0, 'outer_y': 1.0},
        {'pattern': 'QF', 'shape': 'cylinder', 'outer_x': 2.0, 'outer_y': 2.0},
    ]
    elements = [{'name': 'QF', 'length': 0.3}]
    matched = match_apertures(elements, entries, default_hw=0.2)
    assert len(matched) == 1
    assert matched[0]['shape'] == 'block'  # first matching pattern (Q*) wins
