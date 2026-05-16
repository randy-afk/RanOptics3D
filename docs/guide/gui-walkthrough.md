# GUI Walkthrough

The left panel has three tabs. Configure everything here before clicking **▶ Render 3D**.

---

## Input Tab

Select your backend, point to your input file, and set the output directory.

| Control | Description |
|---|---|
| **Simulation Code** | Tao/Bmad, ELEGANT, MAD-X, or xsuite |
| **Input File** | Path to your lattice file — see [Supported Backends](../reference/backends.md) |
| **Output Directory** | Where the generated `.html` file will be saved |
| **▶ Render 3D** | Generate the 3D HTML visualization |

---

## Range & Universes Tab

For multi-universe lattices such as Tao configurations with multiple rings.

| Control | Description |
|---|---|
| **Universe selector** | Choose which universes to include in the plot |
| **s-range** | Restrict the rendered lattice to a specific s interval (meters) |

!!! note
    For single-universe lattices (most ELEGANT and MAD-X cases) this tab can be left at defaults.

---

## Beam & Inspector Tab

| Control | Description |
|---|---|
| **εx, εy** | Horizontal and vertical normalized emittances for beam size calculations |
| **Energy spread** | σ_δ used for the σ tube overlay |
| **Optics panels** | Toggle which plots appear in the Twiss Inspector: β, σ, η, orbit, phase advance |
| **σ tube** | Enable/disable the 3D beam envelope tube overlay |
