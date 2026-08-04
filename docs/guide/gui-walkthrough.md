# GUI Walkthrough

The GUI is split into two panels. The **left panel** controls what to load and how to interpret the beam. The **right panel** controls how the 3D scene is rendered. Configure both before clicking **▶ Render 3D**.

![RanOptics3D GUI](../assets/gui.png)

---

## Header

The header shows the app name/version, author info, and a **☀ Light / 🌙 Dark**
toggle in the top-right — this switches the *application's own* color
theme (kept in sync with RanOptics's palette) and is unrelated to the
**Dark mode** checkbox in the 3D View tab, which controls the background
of the *rendered HTML output* instead. All your current form values, the
output log, and the last-render state carry over across a toggle.

---

## Menu Bar

| Menu | Item | Description |
|---|---|---|
| **File** | Browse Input… | Same as the Input tab's Browse button |
| | Save Output As… | Same as the Input tab's Save as button |
| | Recent Files | Submenu listing recently rendered input files — click one to load it |
| | Copy Output Path | Copies the last rendered HTML's full path to the clipboard |
| **Presets** | Save Current as Preset… | Saves every field on this page (except the input file path and Beam & Inspector fields — see note below) under a name you choose, stored in `~/.ranoptics3d_presets.json` |
| | Load Preset | Submenu listing saved presets — click one to apply it |
| | Delete a preset… | Remove a saved preset by name |
| **Run** | ▶ Run | Same as the bottom bar's Render 3D button |
| | 🔍 Inspect lattice | Same as the bottom bar's Inspect button |

!!! note
    Named presets intentionally don't include the input file path or
    Beam & Inspector tab fields (emittances, Twiss/σ-tube settings) —
    they're meant for reusable *rendering* configurations across
    different lattices. All of this does carry over automatically,
    though, when you use the Light/Dark theme toggle, since that's
    preserving your current session rather than saving a reusable preset.

---

## Left Panel

### Input Tab

Select your backend, point to your input file, and configure output.

| Control | Description |
|---|---|
| **Input file** | Path to your lattice file — see [Supported Backends](../reference/backends.md). Auto-detected from extension: `.init` → Tao, `.ele` → ELEGANT, `.json` → xsuite, `.tfs` → MAD-X |
| **Code backend** | Backend override. Normally auto-detected — only set manually if your file has a non-standard extension |
| **xsuite line name** *(xsuite only)* | Name of the line to load from the Environment JSON. Leave blank to auto-detect (picks the line with the most elements) |
| **Survey file (.tfs)** *(MAD-X only)* | Path to a MAD-X `SURVEY` output file, required for the 3D floor-plan layout — without it the lattice loads but has no spatial position data |
| **Output HTML** | Filename for the generated `.html` file. Open in any browser to view the 3D scene |
| **Save as** | Choose a different output path or filename |
| **Plot title** | Optional title embedded in the rendered HTML |

!!! note
    The xsuite and MAD-X rows only appear when that backend is selected
    (auto-detected from the input file's extension, or set manually via
    Code backend).

---

### Range & Universes Tab

![Range & Universes tab](../assets/gui-range-universes.png)

For multi-universe lattices such as Tao configurations with multiple rings.

| Control | Description |
|---|---|
| **Universe selector** | One checkbox + editable label per universe. Uncheck to exclude a universe from the plot; the label text (used in trace names and the legend) can be edited freely |
| **s-range** | Restrict the rendered lattice to a specific s interval (meters) |

!!! note
    For single-universe lattices (most ELEGANT and MAD-X cases) this tab can be left at defaults.

---

### Beam & Inspector Tab

![Beam & Inspector tab](../assets/gui-beam-inspector.png)

| Control | Description |
|---|---|
| **εx, εy** | Horizontal and vertical geometric emittances (m·rad) used for beam size σ = √(ε·β) in the Twiss Inspector and the 3D σ tube overlay |
| **σ_dp / p** | Momentum spread |
| **Optics panels** | Toggle which plots appear in the Twiss Inspector: β, σ, η (dispersion), orbit, phase advance. β and σ are on by default; σ requires εx/εy to be set, orbit requires `.cen` (ELEGANT) or equivalent |
| **Phase units** | Only affects the phase-advance panel: cumulative radians, or normalized to 0→1 per 2π |
| **Show σ tube in 3D view** | Enable/disable the 3D beam envelope tube overlay (off by default) |
| **Envelope scale** | Multiplier on the tube radius — 1 = 1σ envelope, 3 = 3σ, etc. |
| **Tube opacity** | 0.0–1.0 transparency of the σ tube mesh |
| **Tube segments** | Azimuthal resolution of the tube's circular cross-section — higher is smoother but heavier |
| **σ_x color / σ_y color** | Hex colors for the horizontal/vertical crosshair lines drawn at each element alongside the tube |
| **Magnet size file** | Load a definition file to override element box dimensions — see [Magnet Size File](../reference/magnet-size-file.md) |

---

## Right Panel

### 3D View Tab

Controls the overall appearance and camera behavior of the rendered scene.

#### Axis Aspect & Scale

| Control | Description |
|---|---|
| **Aspect mode** | `data` preserves true proportions. `manual` lets you scale each axis independently using the X/Y/Z scale fields. `cube` forces equal axes (rarely useful) |
| **X / Y / Z scale** | Active only in `manual` mode. Scale < 1 compresses an axis, scale > 1 stretches it. Useful when a lattice is very long in one dimension — e.g. set Z=0.5 to display an 80 m lattice as if it were 40 m long |

#### Camera & Convention

| Control | Description |
|---|---|
| **Camera preset** | Initial view on load: `iso`, `top`, `side`, or `front`. The HTML viewer allows free rotation regardless of this setting |
| **Z-up convention** | When checked, Z is the vertical axis (matches MAD-X surveyors). Default is Y-up, which matches Bmad/pytao |

#### Focus & Pivot

| Control | Description |
|---|---|
| **Focus on element** | Element name to center the rotation pivot on (e.g. `IP1`, `QF12`). Dragging in the browser will orbit around that element instead of the lattice center |
| **Focus radius (m)** | If set, also crops the view to within this radius of the focus element |
| **Camera eye x,y,z** | Override the camera eye position directly. Hover the modebar in any rendered HTML, drag to your preferred view, then read the eye position from the toolbar tooltip and paste here for exact reproducibility |

#### Theme

| Control | Description |
|---|---|
| **Dark mode** | Renders the scene with a dark background |
| **Show XYZ axis gizmo at origin** | Displays a small XYZ orientation indicator at the world origin |
| **Embed live control panel in HTML** | Adds an interactive sidebar to the rendered HTML — no re-render needed to use it. See [Live Control Panel](#live-control-panel) below |
| **Fully self-contained HTML (works offline)** | Off (default): output loads Plotly.js from a CDN — small file, needs internet the first time it's opened. On: embeds Plotly.js directly (~4 MB larger) so the file works with no internet connection at all |

#### Beampipe

| Control | Description |
|---|---|
| **Show beampipe centerline** | Draws a line along the beam path through the lattice |
| **Pipe color** | Hex color for the centerline (default `#888888`) |
| **Width** | Line width of the beampipe centerline |

---

### Elements Tab

![Elements tab](../assets/gui-elements.png)

Controls the geometry and visibility of individual element types in the 3D scene.

#### Element Box Size

| Control | Description |
|---|---|
| **Half-width (m)** | Transverse horizontal half-size of element boxes in beam-frame coordinates. Tune smaller for tight lattices, larger for visibility |
| **Half-height (m)** | Transverse vertical half-size of element boxes |

#### Bend Smoothness

| Control | Description |
|---|---|
| **Segments per bend** | Number of straight segments used to approximate each dipole arc. Higher values produce smoother curves but increase file size and render time |

#### Visibility & Opacity

Each element type (Dipole, Quadrupole, Sextupole, Octupole, Kicker, Monitor, RF Cavity, Solenoid, Marker) has a checkbox and an opacity slider.

| Control | Description |
|---|---|
| **Checkbox** | Uncheck to hide that element type entirely |
| **Opacity** | 0.0–1.0. Partial values fade elements — useful for focusing attention on specific magnet families |
| **Include markers/monitors as boxes** | Markers and monitors are zero-length elements; by default they are not drawn as boxes. Enable this to render them as small boxes |
| **Show element outlines** | Draws white edge lines on element boxes. Turn off to hide segment outlines on curved dipoles for a cleaner look |
| **Realistic magnet shapes** | Off by default (plain boxes). When enabled, quadrupoles/sextupoles/octupoles render as a yoke plate + beam bore + curved pole-piece coils, and dipoles/correctors (kicker/hkicker/vkicker) render as a yoke frame with a visible beam gap and coil accents. Coil windings use a shared copper accent color — see [Element Colors](../reference/element-colors.md). Uncheck to fall back to the simple box rendering if this doesn't suit your lattice |

#### Mirror

| Control | Description |
|---|---|
| **Flip bend direction (mirror X)** | Mirrors the lattice layout along X. Useful when the survey coordinate handedness doesn't match your expected orientation |

---

### Overlays Tab

![Overlays tab](../assets/gui-overlays.png)

Controls additional geometry overlaid on the 3D scene.

#### Element Annotations

| Control | Description |
|---|---|
| **Pattern** | Comma-separated wildcard patterns matching element names (e.g. `IPM*, BPM*, IP*`). Adds floating 3D text labels at all matching elements |
| **Font size** | Size of the 3D annotation text |

#### Tunnel Wall

| Control | Description |
|---|---|
| **Wall coord file** | Path to a `.dat` file defining the tunnel wall geometry. Format: one line per point — `x_in y_in z_in x_out y_out z_out` |
| **Draw tunnel wall** | Enable/disable rendering of the tunnel wall surface |

#### Ground Plane

| Control | Description |
|---|---|
| **Draw ground plane** | Renders a flat ground plane at the specified Y position |
| **Ground Y position** | Vertical position of the ground plane in survey coordinates |
| **Show grid on ground** | Overlays a grid on the ground plane for spatial orientation. Place it at the floor of your tunnel |

---

## Bottom Bar

| Control | Description |
|---|---|
| **▶ Render 3D** | Build the full 3D scene and write the output HTML file |
| **Open in browser** | Open the last rendered HTML file in your default browser |
| **Inspect** | Dry-run that loads the lattice and reports element counts by type without rendering. Useful for verifying the correct file and universe are loaded before a full render |
| **Clear log** | Clear the output log panel |

---

## Live Control Panel

When **Embed live control panel in HTML** is enabled in the 3D View tab, the rendered HTML includes a collapsible sidebar with real-time controls — no re-render required.

| Section | Controls |
|---|---|
| **Element Types** | Per-type visibility checkboxes and opacity sliders — same as the Elements tab but adjustable live in the browser |
| **Highlight Elements** | Wildcard name pattern to highlight matching elements (e.g. `BPM*`, `IP1`) |
| **Camera** | Rotation/zoom instructions, preset view buttons (Iso, Top, Side, Front), and Screenshot |
| **Aspect (X / Y / Z)** | Live axis scale sliders. Compresses or stretches axes without re-rendering. Note: element boxes do not resize — only the spacing scales |
| **Twiss Inspector** | Click any element in the scene to set it as Start or End, then open the inspector. Or type element names or s-values directly |
| **Twiss σ Tube** | Reminder to set εx/εy in the GUI and re-render if no beta data is present |
| **Overlays** | Toggle Beampipe, Axes gizmo, and Grid live |
| **Annotations** | Wildcard pattern for live element labels — updates without re-rendering |
| **Selected Element** | Click any element in the scene to pin its name and properties here |
| **Reset all** | Resets all live panel controls to their render-time defaults |