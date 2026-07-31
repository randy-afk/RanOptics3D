# Changelog

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
