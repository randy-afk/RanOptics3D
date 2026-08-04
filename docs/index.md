# RanOptics3D

An interactive 3D accelerator lattice viewer for accelerator physicists. Reads lattice and
optics data from simulation codes and produces an interactive HTML visualization
with an in-browser control panel.

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
- **Offline HTML option** — embed Plotly.js for a fully self-contained file, or load it from a CDN for a much smaller output
- **Realistic magnet shapes** (opt-in) — quadrupoles/sextupoles/octupoles render as a yoke plate + beam bore + curved pole-piece coils; dipoles and correctors render as a yoke frame with a visible beam gap and coil accents, instead of plain boxes
- **Light/Dark GUI theme** — toggle the application's own color theme from the header, kept in sync with RanOptics's palette; independent of the rendered HTML's own dark-mode setting

---

## Element Color Legend

| Color | Element Type |
|---|---|
| 🔴 Red | Dipoles |
| 🔵 Blue | Quadrupoles |
| 🟡 Yellow | Sextupoles |
| 🟠 Orange | Kickers |
| 🩵 Cyan | RF Cavities |
| 🩷 Pink | Solenoids |
| ⚫ Grey | Markers / Monitors |

With **Realistic magnet shapes** enabled, coil windings render in a
shared copper accent color to contrast against each type's yoke body
color above — see [Element Colors](reference/element-colors.md).

---

!!! note "RanOptics vs RanOptics3D"
    **RanOptics** is the companion 2D optics plotting tool (Twiss, floor plan, etc.).
    **RanOptics3D** is the standalone 3D lattice viewer described in this guide.
    Both share the same backend support and element data model.
