# Changelog

All notable changes to RanOptics3D are documented here.

## [1.0.0] — 2026

### Initial release

**Backends**
- Tao / Bmad via `pytao`
- ELEGANT via `sddsconvert`
- xsuite JSON lattice
- MAD-X TFS files (twiss + optional survey)

**Element rendering**
- Oriented 3D boxes for all element types
- Segmented arc sweep for dipoles (configurable segment count)
- Ellipsoidal pill shape for RF / LC cavities
- Axis-aligned octahedra for markers / monitors (off by default)
- Per-type box edge outlines (darkened match color)

**Interactive HTML control panel**
- Collapsible, positioned at bottom-right edge
- Element type visibility and opacity sliders
- Wildcard element highlight (`BPM*`, `Q?1`) — multi-highlight, colour-coded tags, persists until cleared
- Wildcard annotation labels (comma-separated patterns)
- Camera presets: Iso / Top / Side / Front
- Axis aspect-ratio sliders (X / Y / Z)
- Click-to-pin element info readout
- Reset all button

**PySide6 GUI**
- File picker with recent files
- Backend selector
- s-range filter
- Element width / height controls
- Show markers toggle
- Dark / light mode toggle
- Live log output
- Embedded browser preview tab

**Multi-universe overlay**
- Overlay two lattices in the same 3D scene (different colors/labels per universe)

**Logo**
- Single-line RanOptics3D branding in GUI header

## [1.1.0] — 2026 (refactor)

### Changed
- Split monolithic `ranoptics3d.py` (~4800 lines) into a proper Python package
- Module structure:
  - `ranoptics3d/_elements.py` — element styling, hover, type classification
  - `ranoptics3d/_geometry.py` — 3D mesh geometry builders
  - `ranoptics3d/_backends/` — tao, elegant, xsuite, madx loaders
  - `ranoptics3d/_mesh.py` — beampipe, Twiss tube, element mesh builders
  - `ranoptics3d/_panel/` — HTML template + JS control panel
  - `ranoptics3d/_plot.py` — plot_optics_3d() and utilities
  - `ranoptics3d/_gui.py` — PySide6 GUI
  - `ranoptics3d/cli.py` — CLI entry point
- Installable via `pip install git+https://github.com/randy-afk/ranoptics3d.git`
- JS control panel extracted to `_panel/control.js` for easier editing
- HTML panel extracted to `_panel/panel_template.html`
- Public API unchanged: `from ranoptics3d import plot_optics_3d`
