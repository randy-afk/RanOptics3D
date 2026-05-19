# RanOptics3D

An interactive 3D accelerator lattice viewer for accelerator physicists. Reads lattice and optics data from simulation codes and produces a self-contained interactive HTML visualization with an in-browser control panel.

---

## Features

- **Multi-backend support** — Tao/Bmad, ELEGANT, MAD-X, xsuite
- **Interactive 3D layout** — color-coded elements, beampipe, ground plane, axes gizmo
- **Magnet size file** — override element dimensions per pattern (block or cylinder shapes)
- **Solenoid helix geometry** — solenoids rendered as helical coils
- **Twiss Inspector** — click any element to open an optics popup (β, σ, η, orbit, phase advance)
- **Multi-universe support** — overlay multiple lattices (e.g. Tao multi-universe)
- **Element highlighting** — wildcard pattern search and highlight
- **Annotations** — floating labels on matched elements
- **σ tube overlay** — 3D beam envelope tube along the beampipe
- **Camera presets** — Iso, Top, Side, Front views
- **PNG screenshot** — export the current view
- **Grid toggle** — show/hide axis grid from the HTML panel

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

## Magnet Size File

Override element box dimensions using a definition file:

```
# name      shape      outer_x(cm)   outer_y(cm)
MQA*        cylinder   10.0          10.0
MQB*        block      8.0           12.0
QF          block      8.0
```

- `name` — element name pattern, wildcards `*` and `?` supported
- `shape` — `cylinder` or `block` (default: `block`)
- `outer_x` — horizontal half-width in cm (default: element_half_width × 100)
- `outer_y` — vertical half-height in cm (default: `outer_x`)
- Lines starting with `#` are comments

---

## GUI Overview

### Left Panel

**Input tab** — Select backend, input file, and output path.

**Range & Universes tab** — Select s-range and which universes to plot.

**Beam & Inspector tab** — Set emittances, select Twiss Inspector panels, configure σ tube overlay, load magnet size file.

### In-Browser Control Panel

**Highlight Elements** — Type an element name or wildcard (e.g. `QF*`, `BPM01`) and click ✦ Highlight.

**Camera** — Preset views (Iso, Top, Side, Front) and PNG screenshot.

**Aspect** — Scale X/Y/Z axes independently.

**Overlays** — Toggle beampipe, σ tube, ground plane, axes gizmo, grid, and individual element types.

**Annotations** — Add floating labels to elements matching a pattern.

**Twiss Inspector** — Click elements to set s-range, open optics popup.

**Selected Element** — Click any element to pin its info.

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

- Short solenoids (< ~0.5m) render as a donut shape due to less than one full turn.
- Twiss inspector shows incorrect data for some specific ELEGANT lattices (under investigation).

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

---

## Author

Randika Gamage (randika@jlab.org)  
Good luck, I believe in you
