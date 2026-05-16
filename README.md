# RanOptics3D

**3D Accelerator Lattice Layout Viewer**

A self-contained single-file tool for visualising accelerator beamlines in 3D. Reads survey (floor) coordinates from Tao/Bmad, ELEGANT, xsuite, or MAD-X, renders each element as an oriented 3D shape, and produces an interactive HTML file with a live control panel — no server required.

> Companion to [RanOptics](https://github.com/randy-afk/ranoptics) (2D floor plan viewer).

---

## Features

- **Four backends** — Tao (Bmad), ELEGANT, xsuite, MAD-X TFS
- **Per-element 3D geometry**
  - Dipoles: segmented arc sweep for visible curvature
  - RF / LC cavities: ellipsoidal pill shape
  - Quadrupoles, sextupoles, kickers, …: oriented boxes with edge outlines
  - Markers / monitors: axis-aligned octahedra (optional, off by default)
- **Interactive HTML output** — no server, opens in any browser
- **Live control panel** (bottom-right, collapsible)
  - Show / hide element types, per-type opacity
  - Wildcard element highlight (`BPM*`, `Q?1`, exact name) — multi-highlight with colour-coded tags
  - Annotation labels via wildcard patterns
  - Camera presets (Iso / Top / Side / Front)
  - Axis aspect-ratio sliders
  - Click-to-pin element info
- **PySide6 GUI** — file picker, backend selector, range/filter controls, live log
- **Multi-universe overlay** — compare two lattices in the same scene

---

## Screenshots

<!-- Add screenshots to docs/images/ and uncomment:
![CEBAF full lattice](docs/images/cebaf_full.png)
![GHOST IR final focus](docs/images/ghost_ir.png)
![Control panel](docs/images/control_panel.png)
-->

---

## Requirements

```
numpy
plotly
```

Backend-specific:

| Backend | Requirement |
|---------|-------------|
| Tao / Bmad | `pytao` (`pip install pytao`) |
| ELEGANT | `elegant` + `sddsconvert` on `$PATH` |
| xsuite | `xsuite` (`pip install xsuite`) |
| MAD-X | Run MAD-X yourself; point at `twiss.tfs` (+ optional `survey.tfs`) |

GUI (optional):

```
PySide6
```

Install core dependencies:

```bash
pip install numpy plotly
pip install PySide6          # optional, for GUI
pip install pytao            # optional, for Tao backend
```

---

## Quick Start

### Command line

```bash
# Tao / Bmad
python ranoptics3d.py /path/to/tao.init

# ELEGANT
python ranoptics3d.py /path/to/run.ele --code elegant

# xsuite
python ranoptics3d.py /path/to/lattice.json --code xsuite

# MAD-X (twiss TFS required, survey TFS optional)
python ranoptics3d.py /path/to/twiss.tfs --code madx
python ranoptics3d.py /path/to/twiss.tfs --code madx --survey survey.tfs
```

This writes `lattice3d.html` in the current directory and opens it in your browser.

### Python API

```python
from ranoptics3d import plot_optics_3d

# Minimal
plot_optics_3d('tao.init', output_file='out.html', show=True)

# With options
plot_optics_3d(
    'tao.init',
    output_file       = 'cebaf.html',
    code              = 'tao',
    dark_mode         = True,
    show_markers      = False,
    element_half_width  = 0.25,
    element_half_height = 0.25,
    bend_segments     = 16,
    show              = True,
)
```

### GUI

```bash
python ranoptics3d.py --gui
# or just double-click / run with no arguments
```

---

## CLI Reference

```
usage: ranoptics3d.py [-h] [--code {tao,elegant,xsuite,madx}]
                      [--survey SURVEY] [--output OUTPUT]
                      [--dark] [--no-dark]
                      [--show-markers]
                      [--half-width W] [--half-height H]
                      [--bend-segments N]
                      [--s-start S] [--s-end S]
                      [--gui]
                      [lattice]

positional arguments:
  lattice               Path to lattice file (tao.init, .ele, .json, .tfs)

optional arguments:
  --code                Backend: tao | elegant | xsuite | madx  (default: tao)
  --survey              MAD-X survey TFS file (madx backend only)
  --output              Output HTML path  (default: lattice3d.html)
  --dark / --no-dark    Dark or light background  (default: dark)
  --show-markers        Include marker/monitor elements
  --half-width W        Element box half-width in metres  (default: 0.2)
  --half-height H       Element box half-height in metres  (default: 0.2)
  --bend-segments N     Arc segments per dipole  (default: 12)
  --s-start S           Start s-coordinate (m) for range filter
  --s-end S             End s-coordinate (m) for range filter
  --gui                 Launch PySide6 GUI regardless of other arguments
```

---

## API Reference

### `plot_optics_3d`

```python
plot_optics_3d(
    lattice_file,                  # str | Path
    code                = 'tao',   # 'tao' | 'elegant' | 'xsuite' | 'madx'
    survey_file         = None,    # MAD-X survey TFS (optional)
    output_file         = 'lattice3d.html',
    show                = True,    # open in browser after writing
    dark_mode           = True,
    show_markers        = False,
    element_half_width  = 0.2,     # metres
    element_half_height = 0.2,     # metres
    bend_segments       = 12,      # arc segments per dipole
    s_start             = None,    # range filter start (m)
    s_end               = None,    # range filter end (m)
    focus_element       = None,    # element name — crop view with focus_radius
    focus_radius        = None,    # half-extent (m) for crop window
    annotation_pattern  = None,    # comma-sep wildcard patterns for labels
    visible_types       = None,    # list of legend names to show
    type_opacity        = None,    # dict legend_name -> float opacity
    title               = None,    # plot title
    annotation_font_size= 10,
    log_fn              = None,    # callable(str) for progress messages
)
```

---

## Highlight & Annotation Wildcards

In the live control panel, the **Highlight** field and the **Annotations** field both accept shell-style wildcard patterns:

| Pattern | Matches |
|---------|---------|
| `BPM*` | All elements starting with `BPM` |
| `Q?1` | `QF1`, `QD1`, `QA1`, … |
| `IP1` | Exact match (no wildcards) |
| `BPM*, IPM*` | Multiple patterns, comma-separated (Annotations field) |

Each highlight pattern gets its own colour. The panel tag shows `BPM* (47)` — pattern name plus match count.

---

## Examples

See the [`examples/`](examples/) directory:

- `tao_example.py` — load a Tao lattice and render to HTML
- `elegant_example.py` — load an ELEGANT `.ele` file
- `madx_example.py` — load MAD-X TFS files

---

## Project Structure

```
ranoptics3d/
├── ranoptics3d.py       # Main script (self-contained, ~3900 lines)
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── examples/
│   ├── tao_example.py
│   ├── elegant_example.py
│   └── madx_example.py
└── docs/
    └── images/          # Screenshots (add your own)
```

---

## Contributing

Issues and PRs welcome. Please open an issue before large changes.

---

## License

MIT © 2026 Randika Gamage — Jefferson Lab
