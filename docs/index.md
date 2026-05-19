# RanOptics3D

An interactive 3D accelerator lattice viewer for accelerator physicists. Reads lattice and
optics data from simulation codes and produces a self-contained interactive HTML visualization
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

---

!!! note "RanOptics vs RanOptics3D"
    **RanOptics** is the companion 2D optics plotting tool (Twiss, floor plan, etc.).
    **RanOptics3D** is the standalone 3D lattice viewer described in this guide.
    Both share the same backend support and element data model.
