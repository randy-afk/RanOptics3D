# Supported Backends

## Input Files by Backend

| Backend | Input file | Required outputs |
|---|---|---|
| Tao/Bmad | `tao.init` | — |
| ELEGANT | `run.ele` | `.flr`, `.twi`, `.cen` |
| MAD-X | `lattice.seq` or TFS file | — |
| xsuite | `line.json` | — |

---

## Tao / Bmad

Select **Tao** and point to your `tao.init` file. Multi-universe lattices are supported —
use the **Range & Universes** tab to select which rings to render.

---

## ELEGANT

Select **ELEGANT** and point to your `.ele` run file. The `.flr`, `.twi`, and `.cen`
output files must exist in the same directory (run ELEGANT first).

---

## MAD-X

Select **MAD-X** and point to your sequence file or TFS output. If a separate
`survey.tfs` is needed, place it in the same directory.

---

## xsuite

Select **xsuite** and point to a `line.json` exported from xsuite.

!!! tip "Exporting an xsuite Line"
    ```python
    line.survey()
    line.to_json("line.json")
    ```
