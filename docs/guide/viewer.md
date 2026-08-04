# 3D Viewer

The output is a single HTML file. Open it in any modern browser.
The control panel sits in the bottom-right corner of the page and is collapsible.

By default, the file loads Plotly.js from a CDN — small file, but it needs
an internet connection the first time it's opened. Check **Fully
self-contained HTML** in the GUI (or pass `--offline` on the CLI) to embed
Plotly.js directly instead, at the cost of ~4 MB extra file size. Either
way, the Twiss Inspector's "open in new tab" popup always needs internet —
see [Known Issues](../reference/known-issues.md).

---

## Highlight Elements

Type an element name or wildcard pattern and click **✦ Highlight** to mark matching
elements in the 3D view. Click **✕ Clear all** to reset.

**Pattern examples:**

| Pattern | Matches |
|---|---|
| `QF*` | All elements whose name starts with `QF` |
| `BPM01` | Exact element name |
| `Q?1` | `QF1`, `QD1`, `QA1`, … |

---

## Camera

| Button | View |
|---|---|
| **Iso** | Isometric overview |
| **Top** | Looking straight down |
| **Side** | Lateral view |
| **Front** | End-on view |

The **Screenshot** button saves the current view as a PNG.

---

## Aspect

Scale the X, Y, and Z axes independently. Useful for flat lattices where the default
aspect ratio makes the vertical structure hard to see.

---

## Overlays

Toggle visibility of:

- Beampipe
- σ tube (beam envelope)
- Ground plane
- Axes gizmo
- Grid (Plotly axis grid and background planes)
- Individual element types

---

## Annotations

Type an element name pattern and click **Annotate** to add floating text labels to
matching elements. Multiple comma-separated patterns are supported.

---

## Twiss Inspector

Click any element in the 3D view to set the **Start** or **End** of the s-range,
then click **Open** to launch an optics popup for that range.
See the [Twiss Inspector](twiss-inspector.md) page for details.

---

## Selected Element

Click any element to pin its parameters:

- Name, type, length
- s position
- K1 / K2 / bend angle / voltage (as applicable)
