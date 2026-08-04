"""End-to-end smoke test of plot_optics_3d() through the MAD-X backend.

MAD-X is used here (rather than Tao/ELEGANT/xsuite) because load_madx()
is pure-Python TFS-file parsing with no external binary dependency, so
this test runs in any environment without pytao/elegant/xtrack installed.

This also doubles as the regression test for this session's tunnel-wall
bugfix at the full-pipeline level: before the `import re` fix in _mesh.py,
show_tunnel=True would silently produce no 'Tunnel inner' trace (the
exception was swallowed) instead of raising, so a unit test on
_read_tunnel_wall alone wouldn't necessarily catch a similar wiring
mistake elsewhere in the pipeline — this test exercises the real
plot_optics_3d() call path end to end.
"""
import re

from ranoptics3d._plot import plot_optics_3d

# Matches the specific <script> tag Plotly.py's write_html() generates for
# CDN mode: charset="utf-8", a version-pinned filename, and an integrity
# hash. A plain substring/regex check for "cdn.plot.ly" isn't precise enough
# for two reasons: (1) the embedded Plotly.js bundle itself contains
# "https://cdn.plot.ly/..." as an internal default-config string literal
# (e.g. the topojsonURL default), and (2) control.js's Twiss Inspector
# "open in new tab" popup feature has its own unrelated, hardcoded
# '<script src="https://cdn.plot.ly/plotly-latest.min.js">' JS string that
# it always uses regardless of embed_plotlyjs (a separate, pre-existing
# limitation — that popup opens in its own tab and needs internet either
# way; see known-issues.md).
_CDN_SCRIPT_TAG = re.compile(
    r'<script charset="utf-8" src="https://cdn\.plot\.ly/plotly-[\d.]+\.min\.js"')

_TWISS = (
    '@ NAME %05s "TWISS"\n'
    '* NAME    KEYWORD     S      L     K1L    K2L    ANGLE  TILT   HKICK  VKICK  BETX   BETY   DX  DY  MUX  MUY  X   Y\n'
    '$ %s      %s          %le    %le   %le    %le    %le    %le    %le    %le    %le    %le    %le %le %le  %le  %le %le\n'
    'QF1       QUADRUPOLE  0.5    0.5   0.15   0.0    0.0    0.0    0.0    0.0    10.0   8.0    0.1 0.0 0.1  0.05 0.0 0.0\n'
    'B1        SBEND       1.5    1.0   0.0    0.0    0.1    0.0    0.0    0.0    12.0   9.0    0.2 0.0 0.2  0.10 0.0 0.0\n'
    'BPM1      MONITOR     1.5    0.0   0.0    0.0    0.0    0.0    0.0    0.0    12.0   9.0    0.2 0.0 0.2  0.10 0.0 0.0\n'
)

_SURVEY = (
    '* NAME    X      Y      Z      THETA  PHI\n'
    '$ %s      %le    %le    %le    %le    %le\n'
    'QF1       0.0    0.0    0.5    0.0    0.0\n'
    'B1        0.05   0.0    1.5    0.05   0.0\n'
    'BPM1      0.05   0.0    1.5    0.05   0.0\n'
)

_TUNNEL = "0 -1 0 0 1 0\n1 -1 1 1 1 1\n2 -1 2 2 1 2\n"


def _write_fixtures(tmp_path):
    twiss_path = tmp_path / "twiss.tfs"
    survey_path = tmp_path / "survey.tfs"
    tunnel_path = tmp_path / "tunnel.dat"
    twiss_path.write_text(_TWISS)
    survey_path.write_text(_SURVEY)
    tunnel_path.write_text(_TUNNEL)
    return twiss_path, survey_path, tunnel_path


def test_plot_optics_3d_end_to_end_madx(tmp_path):
    twiss_path, survey_path, tunnel_path = _write_fixtures(tmp_path)
    out_html = tmp_path / "out.html"

    fig = plot_optics_3d(
        str(twiss_path), code='madx', madx_survey=str(survey_path),
        tunnel_wall_file=str(tunnel_path), show_tunnel=True,
        output_file=str(out_html), show=False, add_control_panel=True,
        emit_x=1e-9, emit_y=1e-9, show_twiss=True,
    )

    trace_names = {t.name for t in fig.data}
    assert 'Quadrupole' in trace_names
    assert 'Dipole' in trace_names
    assert 'Beampipe' in trace_names

    # Regression check: tunnel wall must actually render (see module docstring).
    assert 'Tunnel inner' in trace_names
    assert 'Tunnel outer' in trace_names

    assert out_html.exists()
    assert out_html.stat().st_size > 1000  # non-trivially sized HTML output


def test_plot_optics_3d_realistic_magnets_end_to_end(tmp_path):
    """realistic_magnets=True must render successfully through the full
    pipeline (not just at the _build_element_meshes unit level) and the
    resulting mesh traces must still have valid, in-bounds face indices."""
    twiss_path, survey_path, _ = _write_fixtures(tmp_path)
    out_html = tmp_path / "realistic.html"

    fig = plot_optics_3d(
        str(twiss_path), code='madx', madx_survey=str(survey_path),
        output_file=str(out_html), show=False, add_control_panel=False,
        realistic_magnets=True,
    )

    trace_names = {t.name for t in fig.data}
    assert 'Quadrupole' in trace_names
    assert 'Dipole' in trace_names

    for trace in fig.data:
        if trace.type != 'mesh3d':
            continue
        n_verts = len(trace.x)
        all_idx = list(trace.i) + list(trace.j) + list(trace.k)
        assert max(all_idx) < n_verts, f"{trace.name}: face index out of bounds"
        assert min(all_idx) >= 0

    assert out_html.exists()


def test_plot_optics_3d_without_control_panel_still_returns_figure(tmp_path):
    twiss_path, survey_path, tunnel_path = _write_fixtures(tmp_path)
    out_html = tmp_path / "out.html"

    fig = plot_optics_3d(
        str(twiss_path), code='madx', madx_survey=str(survey_path),
        output_file=str(out_html), show=False, add_control_panel=False,
    )
    assert fig is not None
    assert out_html.exists()


def test_plot_optics_3d_auto_detects_code_from_extension(tmp_path):
    twiss_path, survey_path, _ = _write_fixtures(tmp_path)
    tfs_path = tmp_path / "twiss.tfs"  # already has .tfs suffix -> auto = madx
    out_html = tmp_path / "out.html"

    fig = plot_optics_3d(
        str(tfs_path), code='auto', madx_survey=str(survey_path),
        output_file=str(out_html), show=False, add_control_panel=False,
    )
    assert fig is not None


def test_embed_plotlyjs_false_produces_small_cdn_based_html(tmp_path):
    twiss_path, survey_path, _ = _write_fixtures(tmp_path)
    out_html = tmp_path / "cdn.html"

    plot_optics_3d(
        str(twiss_path), code='madx', madx_survey=str(survey_path),
        output_file=str(out_html), show=False, add_control_panel=False,
        embed_plotlyjs=False,
    )
    text = out_html.read_text()
    assert _CDN_SCRIPT_TAG.search(text)
    assert out_html.stat().st_size < 500_000  # no embedded ~4 MB bundle


def test_embed_plotlyjs_true_produces_large_offline_html(tmp_path):
    twiss_path, survey_path, _ = _write_fixtures(tmp_path)
    out_html = tmp_path / "embed.html"

    plot_optics_3d(
        str(twiss_path), code='madx', madx_survey=str(survey_path),
        output_file=str(out_html), show=False, add_control_panel=False,
        embed_plotlyjs=True,
    )
    text = out_html.read_text()
    assert not _CDN_SCRIPT_TAG.search(text)
    assert out_html.stat().st_size > 1_000_000  # embedded Plotly.js bundle


def test_embed_plotlyjs_option_applies_with_control_panel_too(tmp_path):
    """embed_plotlyjs must be honored on both write_html code paths —
    add_control_panel=True (splices the panel into a buffered write_html
    call) and add_control_panel=False (writes directly to output_file)."""
    twiss_path, survey_path, _ = _write_fixtures(tmp_path)
    out_html = tmp_path / "panel_embed.html"

    plot_optics_3d(
        str(twiss_path), code='madx', madx_survey=str(survey_path),
        output_file=str(out_html), show=False, add_control_panel=True,
        embed_plotlyjs=True,
    )
    text = out_html.read_text()
    assert not _CDN_SCRIPT_TAG.search(text)
    assert out_html.stat().st_size > 1_000_000
