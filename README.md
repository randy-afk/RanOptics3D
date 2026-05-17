# RanOptics3D

An interactive 3D accelerator lattice viewer for accelerator physicists. Reads lattice and optics data from simulation codes and produces a self-contained interactive HTML visualization with an in-browser control panel.

---

## Features

- **Multi-backend support** — Tao/Bmad, ELEGANT, MAD-X, xsuite
- **Interactive 3D layout** — color-coded elements, beampipe, ground plane, axes gizmo
- **Twiss Inspector** — click any element to open an optics popup (β, σ, η, orbit, phase advance)
- **Multi-universe support** — overlay multiple lattices (e.g. Tao multi-universe)
- **Element highlighting** — wildcard pattern search and highlight
- **Annotations** — floating labels on matched elements
- **Solenoid helix geometry** — solenoids rendered as helical coils
- **σ tube overlay** — 3D beam envelope tube along the beampipe
- **Camera presets** — Iso, Top, Side, Front views
- **PNG screenshot** — export the current view

---

## Installation

No installation required. Run directly from the repository:

```bash
cd pkg/
python -m ranoptics3d
# or
python RanOptics3D.py
```

### Dependencies

```bash
pip install plotly numpy PySide6
```

For Tao/Bmad backend:
```bash
pip install pytao
```

---

## Usage

### GUI

Launch the GUI and configure from the interface:

```bash
python RanOptics3D.py
```

1. Select your simulation code (Tao, ELEGANT, MAD-X, xsuite)
2. Point to your input file
3. Set output directory
4. Click **▶ Render 3D**

The output is a self-contained HTML file that opens in any browser.

### Input Files by Backend

| Backend | Input file | Required outputs |
|---------|-----------|-----------------|
| Tao/Bmad | `tao.init` | — |
| ELEGANT | `run.ele` | `.flr`, `.twi`, `.cen` |
| MAD-X | `lattice.seq` or TFS file | — |
| xsuite | `line.json` | — |

---

## GUI Overview

### Left Panel

**Input tab** — Select backend, input file, and output path.

**Range & Universes tab** — Select s-range and which universes to plot (for multi-universe Tao lattices).

**Beam & Inspector tab** — Set emittances (εx, εy) and energy spread. Select which optics panels to show in the Twiss Inspector. Toggle the σ tube overlay.

### In-Browser Control Panel

**Highlight Elements** — Type an element name or wildcard (e.g. `QF*`, `BPM01`) and click ✦ Highlight to mark matching elements in the 3D view.

**Camera** — Preset views (Iso, Top, Side, Front) and PNG screenshot.

**Aspect** — Scale X/Y/Z axes independently for flat or elongated lattices.

**Overlays** — Toggle beampipe, σ tube, ground plane, axes gizmo, and individual element types.

**Annotations** — Add floating text labels to elements matching a pattern.

**Twiss Inspector** — Click elements in the 3D view to set a start/end s-range, then open a popup with optics plots for that range.

**Selected Element** — Click any element to pin its info (name, type, length, K1, angle, s-position).

---

## Navigation

| Action | Control |
|--------|---------|
| Rotate | Left drag |
| Pan | Right drag |
| Zoom | Scroll |

---

## Element Colors

| Color | Element type |
|-------|-------------|
| Red | Dipoles |
| Blue | Quadrupoles |
| Yellow | Sextupoles |
| Orange | Kickers |
| Cyan | RF Cavities |
| Pink | Solenoids |
| Grey | Markers / Monitors |

---

## Known Issues

- Short solenoids (< ~0.5m) render as a donut shape rather than a helix due to having less than one full turn.
- Twiss inspector optics show incorrect data for some specific ELEGANT lattices (element ordering issue — under investigation).

---

## Author

Randika Gamage (randika@jlab.org)

## Support

Good luck, I believe in you.
