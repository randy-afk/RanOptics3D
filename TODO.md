# TODO

- **Twiss Inspector popup always needs internet.** The "open in new tab"
  popup in `control.js` (`_openTwissPopup`) builds its HTML with a
  hardcoded `<script src="https://cdn.plot.ly/plotly-latest.min.js">` tag,
  so it requires internet access even when the main output was rendered
  with the offline/self-contained option (`embed_plotlyjs=True`). Fixing
  this means reworking how that popup gets its copy of Plotly.js — it's a
  separate browser tab opened from a `Blob` URL with no shared JS context
  with the parent page, so it can't currently reuse the parent's embedded
  bundle. See `docs/reference/known-issues.md`.
