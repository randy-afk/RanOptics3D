# Changelog

## [1.4.0] - 2026-07-31

### New Features
- **Light/Dark GUI theme** — the application's own chrome now has a full light theme to go with dark, plus a "☀ Light / 🌙 Dark" toggle in the header (kept in sync with RanOptics's `core/themes.py` palette, including its newer semantic colors: `PANEL2`, `ACCENTH`, `AINK`, `ASOFT`, `COPPER`, `CSOFT`). This is independent of the existing "Dark mode" checkbox in the 3D View tab, which still only controls the rendered HTML output's background. Toggling rebuilds the window with fresh colors and preserves all current form values, the output log, and the last-render/open-button state — see `_gui.py`'s `_rebuild_ui()`/`_collect_full_state()`/`_apply_full_state()`.

### Fixed
- The "Range & Universes" and "Beam & Inspector" tab labels rendered as "Range_Universes" / "Beam_Inspector" — Qt was interpreting the unescaped `&` as a mnemonic accelerator (swallowing the character and underlining the next letter). Escaped as `&&` so a literal `&` displays. Found from user-supplied screenshots of the actual running GUI.

### Documentation
- `docs/guide/gui-walkthrough.md` was missing several real controls that predate this session's work: the xsuite line name / MAD-X survey file fields on the Input tab, the fact that universe labels are editable, the Phase units dropdown and all five σ-tube overlay fields (envelope scale, opacity, segments, σ_x/σ_y color) on the Beam & Inspector tab, and the entire File/Presets/Run menu bar. Also added the "Fully self-contained HTML" row to the Theme table, missed when that feature was documented earlier. Found via a direct audit of `_gui.py`'s widget-building code against the docs.

### Internal
- `_theme.py` rewritten to mirror RanOptics's dynamic `_DARK`/`_LIGHT` dict + `apply_theme(mode)` pattern instead of a static one-time palette; `_gui.py` now re-syncs its own module globals from `_theme` on every toggle rather than doing a one-shot `from ._theme import BG, ...` (which would have gone stale the moment the theme switched).
- Several `color: {CRUST}` uses that were actually "text drawn on an accent-colored background" (Run button, success button, section-header pills) now use the semantically-correct `AINK` instead, matching RanOptics's own convention.
- `cli.py`'s inline `QPalette` role-mapping moved into a shared `_theme.apply_qpalette()` so both app startup and the new toggle use the same code.
- Verified via a headless `QT_QPA_PLATFORM=offscreen` smoke test (GUI code itself stays outside the automated pytest suite, per this project's existing testing scope) exercising repeated toggles, state preservation, and stylesheet/menu-bar correctness.

## [1.3.0] - 2026-07-31

### New Features
- **Realistic magnet shapes** (opt-in) — new `realistic_magnets` parameter (GUI: "Realistic magnet shapes" checkbox in the Elements tab; CLI: `--realistic-magnets`). Quadrupoles/sextupoles/octupoles render as a flat yoke plate + central beam bore + curved pole-piece "coil" brackets, modeled after the classic multipole-magnet illustration, instead of plain boxes. Dipoles render as a closed yoke frame with a visible beam-channel gap and coil accents. Correctors (kicker/hkicker/vkicker) — physically small dipoles — get the same dipole yoke shape. Coil-winding faces render in a shared copper accent color (`#c9852f`) via Plotly's per-face `facecolor`, contrasting against each type's own yoke-body color. Off by default; the fallback box rendering is byte-for-byte unchanged from before this feature.

### Fixed
- `_aperture_cylinder_mesh`'s entry/exit cap fan triangles had inverted winding — normals pointed into the tube instead of away from it. Pre-existing, unrelated to this session's other work; affects the `_mag_shape='cylinder'` magnet-size-file override and the new magnet-shape bore geometry. Fixed and added a regression test.

### Internal
- New geometry primitives in `_geometry.py`: `_quad_prism_mesh`/`_quad_prism_edges` (a `_box_mesh` generalized to any convex quadrilateral cross-section), `_curved_bracket_mesh`/`_curved_bracket_edges` (curved pole pieces approximated by chained straight segments, the same technique already used for bent dipoles), and `_concat_meshes_tagged` (per-face body/coil tagging for multi-color composite shapes). All still composed entirely of the same proven box/prism winding topology — no new triangulation risk.
- Added ~15 new tests covering the new geometry (index-bounds, non-degenerate-triangle, and outward-normal integrity checks) and the per-face coloring / corrector-as-dipole behavior in `_build_element_meshes`.

## [1.2.0] - 2026-07-31

### New Features
- **Offline HTML option** — new `embed_plotlyjs` parameter (GUI: "Fully self-contained HTML" checkbox in the 3D View tab; CLI: `--offline`) controls whether the output HTML embeds Plotly.js directly (~4 MB larger, works with no internet connection) or loads it from a CDN (small file, needs internet on first view — the previous, still-default behavior). Also fixes a prior inconsistency where `add_control_panel=False` silently produced a fully-embedded file while `add_control_panel=True` silently forced CDN mode, regardless of user intent.

### Fixed
- Tunnel wall rendering (`show_tunnel` / `tunnel_wall_file`) was completely broken — `_mesh.py` used `re.split()` without importing `re`, so every call raised internally and was silently swallowed by a broad exception handler. The wall never rendered and no error surfaced anywhere in the UI.
- `pip install .` and `pip install -e .` failed unconditionally on any modern pip/setuptools due to an invalid `build-backend` in `pyproject.toml` (`setuptools.backends.legacy:build`, which does not exist). Corrected to `setuptools.build_meta`.
- Fixed `pyproject.toml` package version (`1.0.0`) being out of sync with the actual release (`1.1.0`, per `ranoptics3d/__init__.py` and this changelog).

### Known Limitations
- The Twiss Inspector's "open in new tab" popup always loads Plotly.js from a CDN and needs internet, even when the main output was rendered with `embed_plotlyjs=True`. See `docs/reference/known-issues.md`.

### Internal
- Added a pytest test suite (`tests/`) covering mesh/geometry math, element classification, aperture-file parsing, mesh assembly, plot helper functions, backend file parsers, and end-to-end MAD-X pipeline smoke tests (including the CDN-vs-embedded-Plotly.js behavior).
- Added GitHub Actions CI (`.github/workflows/tests.yml`) running the test suite across Python 3.9–3.12, plus a separate `ruff` lint job.
- Removed ~220 lines of dead, duplicated mesh-geometry code from `_elements.py` (the live versions already lived in `_geometry.py`) and cleaned up unused imports flagged by `ruff`.

## [1.1.0] - 2026-05-18

### New Features
- **Magnet size file** — load a definition file to override element box dimensions per element pattern. Supports `block` and `cylinder` shapes with `outer_x` / `outer_y` in cm. Wildcard patterns supported.
- **Solenoid geometry** — solenoids rendered as helical coils (`SOLE` and `Solenoid` key names supported).
- **Element outline toggle** — checkbox in GUI and HTML panel to show/hide white edge outlines on elements.
- **Grid toggle in HTML panel** — checkbox in the Overlays section to show/hide the Plotly axis grid and background planes.
- **Element key normalization** — ELEGANT truncated element names (`SOLE`, `DRIF`, `SBEN`, `QUAD`, etc.) now correctly mapped to full type names.
- **Improved shading** — `flatshading=False` for smoother 3D appearance.

### Bug Fixes
- Horizontal dipole bend direction corrected for ELEGANT lattices (was bending opposite direction).
- Beampipe now renders correctly in all universes of multi-universe Tao plots.
- Twiss inspector optics now use parallel arrays (`optics_series`) — fixes interleaving spikes in multi-universe plots.
- JS syntax error (stray `)`) in `control.js` that was breaking click-to-select and autocomplete.
- Solenoid elements not appearing due to missing entry in GUI element type list.
- Magnet size override now applied before mesh building (was applied after, causing no effect).

## [1.0.0] - 2026-05-08

- Initial release
- Tao/Bmad, ELEGANT, MAD-X, xsuite backends
- Interactive 3D HTML output with in-browser control panel
- Twiss Inspector popup with beta, sigma, dispersion, orbit, phase advance
- Multi-universe support
- Element highlighting, annotations, camera presets, PNG screenshot
