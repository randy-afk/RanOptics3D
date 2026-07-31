"""
ranoptics3d._elements
=====================
Element styling, hover tooltip builder, and type classification.
"""
from __future__ import annotations
import numpy as np

# Color scheme matches RanOptics 2D floor plan
_ELEMENT_COLORS = {
    'sbend':       '#d62728',  # red
    'rbend':       '#d62728',
    'quadrupole':  '#1f77b4',  # blue
    'sextupole':   '#2ca02c',  # green
    'octupole':    '#9467bd',  # purple
    'kicker':      '#ff7f0e',  # orange
    'hkicker':     '#ff7f0e',
    'vkicker':     '#ff7f0e',
    'monitor':     '#9467bd',  # purple
    'instrument':  '#9467bd',
    'rfcavity':    '#17becf',  # cyan
    'lcavity':     '#17becf',
    'solenoid':    '#e377c2',  # pink/magenta
    'marker':      '#888888',  # gray
}

_ELEMENT_LEGEND_NAME = {
    'sbend': 'Dipole', 'rbend': 'Dipole',
    'quadrupole': 'Quadrupole',
    'sextupole': 'Sextupole', 'octupole': 'Octupole',
    'kicker': 'Kicker', 'hkicker': 'Kicker', 'vkicker': 'Kicker',
    'monitor': 'Monitor', 'instrument': 'Monitor',
    'rfcavity': 'RF Cavity', 'lcavity': 'RF Cavity',
    'solenoid': 'Solenoid',
    'marker': 'Marker',
}

FULL_WIDTH_TYPES = ('sbend', 'rbend', 'quadrupole')
THIN_ELEMENT_THRESHOLD = 1e-3
_MARKER_MONITOR_KEYS = {'marker', 'monitor', 'hmon', 'vmon', 'instrument', 'bpm'}


_KEY_ALIASES = {
    'sole':       'solenoid',
    'drif':       'drift',
    'sben':       'sbend',
    'rben':       'rbend',
    'quad':       'quadrupole',
    'sext':       'sextupole',
    'octu':       'octupole',
    'rfca':       'rfcavity',
    'lcav':       'lcavity',
    'kick':       'kicker',
    'hkic':       'hkicker',
    'vkic':       'vkicker',
    'moni':       'monitor',
    'inst':       'instrument',
    'mark':       'marker',
}

def _normalize_key(key):
    """Normalize element key — handles ELEGANT's 4-char truncated names."""
    k = key.lower().strip()
    return _KEY_ALIASES.get(k, k)


def element_color(key):
    k = _normalize_key(key)
    for prefix, color in _ELEMENT_COLORS.items():
        if prefix in k:
            return color
    return None


def element_legend(key):
    k = _normalize_key(key)
    for prefix, name in _ELEMENT_LEGEND_NAME.items():
        if prefix in k:
            return name
    return None


def make_hover(elem):
    """Build the hover tooltip HTML for one element."""
    name = elem['name'].split('\\')[-1]
    key = elem['key']
    L = elem['length']
    k1 = elem.get('k1', 0.0)
    k2 = elem.get('k2', 0.0)
    angle = elem.get('angle', 0.0)
    raw_angle = elem.get('raw_angle', angle)
    s0 = elem['s_start']
    kc = _normalize_key(key)
    lines = [
        f'<b>{name}</b>',
        f'<i>{key}</i>',
        f'L = {L:.4f} m',
        f's_start = {s0:.4f} m',
        f's_end &nbsp;= {s0 + L:.4f} m',
    ]
    if 'sbend' in kc or 'rbend' in kc:
        rt = elem.get('ref_tilt', 0.0)
        bend_plane = 'Vertical' if abs(abs(rt) - np.pi / 2) < 0.01 else 'Horizontal'
        lines.append(f'Bend plane: {bend_plane}')
        lines.append(f'Angle = {np.degrees(raw_angle):.4f}°')
        if abs(raw_angle) > 1e-9:
            lines.append(f'ρ = {abs(L / raw_angle):.4f} m')
    if 'quadrupole' in kc:
        lines.append(f'K1 = {k1:.6f} m⁻²')
    if 'sextupole' in kc:
        lines.append(f'K2 = {k2:.6f} m⁻³')
    if kc == 'kicker':
        lines += [
            f'hkick = {elem.get("hkick", 0):.6f}',
            f'vkick = {elem.get("vkick", 0):.6f}',
        ]
    elif kc in ('hkicker', 'vkicker'):
        lines.append(f'kick = {elem.get("kick", 0):.6f}')
    if 'rfcavity' in kc or 'lcavity' in kc:
        v = elem.get('voltage', 0.0)
        f = elem.get('frequency', 0.0)
        if v:
            lines.append(f'V = {v / 1e6:.3f} MV' if abs(v) >= 1e6 else f'V = {v:.1f} V')
        if f:
            lines.append(f'f = {f / 1e9:.4f} GHz' if f >= 1e9 else f'f = {f / 1e6:.4f} MHz')
    # Position info for 3D
    if 'flr_x0' in elem:
        x0 = elem['flr_x0']; y0 = elem['flr_y0']; z0 = elem['flr_z0']
        lines.append(f'pos = ({x0:.3f}, {y0:.3f}, {z0:.3f})')
    return '<br>'.join(lines) + '<extra></extra>'

