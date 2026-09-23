# Changelog

---

## v1.5.1 — 2026-09-23

### Fixed

- The standalone executable crashed on every render with a missing `panel_template.html` error — the build workflow's data-bundling step silently packaged nothing for `ranoptics3d`'s own resource files. Fixed by bundling them explicitly. Found via real macOS beta testing of the v1.5.0 release.

---

## v1.5.0 — 2026-09-22

### New Features

- **Bmad library path override** — new "Bmad library" / "Extra library dirs" fields on the Input tab (Tao backend only; CLI: `--bmad-lib` / `--bmad-extra-paths`) let you point RanOptics3D at an explicit Bmad shared library, bypassing `pytao`'s own auto-discovery. Mainly needed for the new standalone executable, which has no way to find a Bmad install on its own. Both fields save automatically and are remembered across launches.
- **Standalone executable releases** — Linux/Windows/macOS binaries are now built automatically via GitHub Actions on every published release, using the same PyInstaller + Bmad-library-staging approach already proven on RanOptics (2D).

---

## v1.4.0 — 2026-07-31

### New Features

- **Light/Dark GUI theme** — the application's own chrome now has a full light theme to go with dark, plus a "☀ Light / 🌙 Dark" toggle in the header (kept in sync with RanOptics's palette, including its newer semantic colors). Independent of the existing "Dark mode" checkbox in the 3D View tab, which still only controls the rendered HTML output's background. Toggling preserves all current form values, the output log, and the last-render/open-button state.

### Fixed

- The "Range & Universes" and "Beam & Inspector" tab labels rendered as "Range_Universes" / "Beam_Inspector" — Qt was treating the unescaped `&` as a mnemonic accelerator. Escaped as `&&`.

### Documentation

- [GUI Walkthrough](guide/gui-walkthrough.md) was missing several real controls: the xsuite/MAD-X-specific Input tab fields, editable universe labels, the Phase units dropdown and σ-tube overlay fields on Beam & Inspector, the "Fully self-contained HTML" checkbox, and the entire File/Presets/Run menu bar.

### Internal

- `_theme.py` now mirrors RanOptics's dynamic theme-switching pattern instead of a static one-time palette.
- Fixed a few spots that were reusing `CRUST` (menubar/statusbar background) for "text on an accent-colored background," now using the semantically-correct `AINK`.
- `cli.py`'s palette setup now shares code with the new toggle instead of duplicating it.

---

## v1.3.0 — 2026-07-31

### New Features

- **Realistic magnet shapes** (opt-in) — new `realistic_magnets` parameter (GUI: "Realistic magnet shapes" checkbox in the Elements tab; CLI: `--realistic-magnets`). Quadrupoles/sextupoles/octupoles render as a flat yoke plate + central beam bore + curved pole-piece "coil" brackets, modeled after the classic multipole-magnet illustration, instead of plain boxes. Dipoles render as a closed yoke frame with a visible beam-channel gap and coil accents. Correctors (kicker/hkicker/vkicker) — physically small dipoles — get the same dipole yoke shape. Coil-winding faces render in a shared copper accent color (`#c9852f`), contrasting against each type's own yoke-body color. Off by default; the fallback box rendering is unchanged.

### Fixed

- `_aperture_cylinder_mesh`'s entry/exit cap fan triangles had inverted winding — normals pointed into the tube instead of away from it. Affects the `_mag_shape='cylinder'` magnet-size-file override and the new magnet-shape bore geometry.

### Internal

- New geometry primitives: a generalized box-to-any-convex-quadrilateral prism, curved pole-piece brackets (chained straight segments, same technique as bent dipoles), and per-face body/coil color tagging for multi-color composite shapes.
- ~15 new tests covering geometry integrity (index-bounds, non-degenerate-triangle, outward-normal checks) and the new per-face coloring / corrector-as-dipole behavior.

---

## v1.2.0 — 2026-07-31

### New Features

- **Offline HTML option** — new `embed_plotlyjs` parameter (GUI: "Fully self-contained HTML" checkbox in the 3D View tab; CLI: `--offline`) controls whether the output HTML embeds Plotly.js directly (~4 MB larger, works with no internet connection) or loads it from a CDN (small file, needs internet on first view — the previous, still-default behavior).

### Fixed

- Tunnel wall rendering (`show_tunnel` / `tunnel_wall_file`) was completely broken — `_mesh.py` used `re.split()` without importing `re`, so every call raised internally and was silently swallowed by a broad exception handler. The wall never rendered and no error surfaced anywhere in the UI.
- `pip install .` and `pip install -e .` failed unconditionally on any modern pip/setuptools due to an invalid `build-backend` in `pyproject.toml` (`setuptools.backends.legacy:build`, which does not exist). Corrected to `setuptools.build_meta`.
- Fixed `pyproject.toml` package version (`1.0.0`) being out of sync with the actual release (`1.1.0`).

### Known Limitations

- The Twiss Inspector's "open in new tab" popup always loads Plotly.js from a CDN and needs internet, even when the main output was rendered with the offline/self-contained option. See [Known Issues](reference/known-issues.md).

### Internal

- Added a pytest test suite (`tests/`) covering mesh/geometry math, element classification, aperture-file parsing, mesh assembly, plot helper functions, backend file parsers, and end-to-end MAD-X pipeline smoke tests (including the CDN-vs-embedded-Plotly.js behavior).
- Added GitHub Actions CI running the test suite across Python 3.9–3.12, plus a separate `ruff` lint job.
- Removed dead, duplicated mesh-geometry code and unused imports flagged by `ruff`.

---

## v1.1.0 — 2026-05-18

### New Features

- **Magnet size file** — load a definition file to override element box dimensions per element pattern. Supports `block` and `cylinder` shapes with `outer_x` / `outer_y` in cm. Wildcard patterns supported.
- **Solenoid geometry** — solenoids rendered as helical coils (`SOLE` and `Solenoid` key names supported).
- **Element outline toggle** — checkbox in GUI and HTML panel to show/hide white edge outlines on elements.
- **Grid toggle** — checkbox in the Overlays section of the HTML panel to show/hide the Plotly axis grid and background planes.
- **Element key normalization** — ELEGANT truncated element names (`SOLE`, `DRIF`, `SBEN`, `QUAD`, etc.) now correctly mapped to full type names.
- **Improved shading** — `flatshading=False` for smoother 3D appearance.

### Bug Fixes

- Horizontal dipole bend direction corrected for ELEGANT lattices (was bending in the wrong direction).
- Beampipe now renders correctly in all universes of multi-universe Tao plots.
- Twiss Inspector optics now use parallel arrays (`optics_series`) — fixes interleaving spikes in multi-universe plots.
- JS syntax error (stray `)`) in `control.js` that was breaking click-to-select and autocomplete.
- Solenoid elements not appearing due to missing entry in GUI element type list.
- Magnet size override now applied before mesh building (was applied after, causing no effect).

---

## v1.0.0 — 2026-05-08

*Initial release.*

- Tao/Bmad, ELEGANT, MAD-X, xsuite backends
- Interactive 3D HTML output with in-browser control panel
- Twiss Inspector popup with β, σ, η, orbit, phase advance
- Multi-universe support
- Element highlighting, annotations, camera presets, PNG screenshot
