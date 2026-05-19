# Changelog

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
