"""
ranoptics3d._panel.builder
===========================
Builds the in-browser control panel — HTML + JS — injected into
the Plotly HTML output.  The JS is loaded from control.js and the
HTML template from panel_template.html so they can be edited
independently without touching Python code.
"""
from __future__ import annotations
import json
from importlib.resources import files


def _load_resource(filename: str) -> str:
    """Load a text resource file bundled with this package."""
    return files(__package__).joinpath(filename).read_text(encoding='utf-8')


def build_control_panel(scene_data: dict, dark_mode: bool = True):
    """Return (panel_html, post_script_js) to inject into the Plotly HTML.

    panel_html      — the floating control panel div + CSS
    post_script_js  — the JS that wires up all the controls

    scene_data keys:
        elements, type_traces, type_colors, overlay_traces,
        axis_ranges, axis_halfext, aspect_ratio, data_extent,
        eyes, dark_mode, annot_font_size, emit_x, emit_y,
        inspector_plots, phase_normalized
    """
    panel_bg   = 'rgba(30,30,30,0.92)' if dark_mode else 'rgba(255,255,255,0.95)'
    panel_fg   = '#eee'  if dark_mode else '#222'
    panel_dim  = '#888'  if dark_mode else '#666'
    accent     = '#fda769'
    border     = '#555'  if dark_mode else '#bbb'
    input_bg   = 'rgba(0,0,0,0.3)' if dark_mode else 'rgba(0,0,0,0.05)'

    json_blob = json.dumps(scene_data).replace('</', '<\\/')

    # Load HTML template and JS from package resources
    html_template = _load_resource('panel_template.html')
    js_template   = _load_resource('control.js')

    # Apply f-string style substitutions to the HTML template
    panel_html = html_template.format(
        panel_bg=panel_bg, panel_fg=panel_fg, panel_dim=panel_dim,
        accent=accent, border=border, input_bg=input_bg,
    )

    post_script = js_template.replace('__SCENE_JSON__', json_blob)

    return panel_html, post_script
