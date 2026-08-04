# Element Colors

Elements are color-coded by type throughout the 3D scene.

| Color | Element Type |
|---|---|
| 🔴 **Red** | Dipoles |
| 🔵 **Blue** | Quadrupoles |
| 🟡 **Yellow** | Sextupoles |
| 🟠 **Orange** | Kickers |
| 🩵 **Cyan** | RF Cavities |
| 🩷 **Pink** | Solenoids |
| ⚫ **Grey** | Markers / Monitors |

!!! note
    Elements not matching any of the above categories are rendered in neutral grey
    and are still fully clickable with correct attributes in the Selected Element panel.

## Realistic Magnet Shapes — Coil Color

When **Realistic magnet shapes** is enabled (see
[GUI Walkthrough](../guide/gui-walkthrough.md#visibility-opacity)), each
magnet's coil-winding faces render in a shared copper accent
(`#c9852f`), regardless of type, so they read as visually distinct from
the yoke body's type color above — the same way a real magnet's copper
coils contrast with its steel yoke. This applies to quadrupoles,
sextupoles, octupoles, dipoles, and correctors (kicker/hkicker/vkicker,
which render with the same yoke shape as a dipole since they're
physically small dipoles).
