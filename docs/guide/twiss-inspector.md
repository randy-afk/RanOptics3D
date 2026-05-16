# Twiss Inspector

The Twiss Inspector lets you examine optics plots for any segment of the lattice
by clicking directly in the 3D view.

---

## Setting the s-Range

1. Click an element in the 3D scene to select it.
2. In the Twiss Inspector panel, click **Set Start** or **Set End**.
3. Repeat for the other boundary.
4. Click **Open** to launch the optics popup.

!!! tip
    Start and End can be set in either order — the Inspector always plots
    from the lower s value to the higher one.

---

## Available Optics Panels

Which panels appear is controlled by the toggles in the
[Beam & Inspector tab](gui-walkthrough.md#beam--inspector-tab) before rendering.

| Panel | Description |
|---|---|
| **β** | Horizontal and vertical beta functions (m) |
| **σ** | Beam size σ_x, σ_y (mm), from emittance and β |
| **η** | Dispersion η_x, η_y (m) |
| **Orbit** | Closed orbit x, y (mm) |
| **Phase advance** | Cumulative μ_x, μ_y (2π) |

---

!!! note "Plotly toolbar"
    The Plotly toolbar appears in the **top-right corner** of the popup when the
    mouse is anywhere over the plot area. It disappears when the cursor leaves.
    On tall dashboards, scroll to the top to access it.

!!! warning "Known issue"
    The Twiss Inspector shows incorrect data (spikes) for some specific ELEGANT
    lattices. This is an element-ordering issue under investigation.
    See [Known Issues](../reference/known-issues.md) for details.
