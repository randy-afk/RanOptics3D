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

### Bmad library path

RanOptics3D loads Tao/Bmad through `pytao`, which normally auto-discovers your Bmad
install with no configuration needed. The **Bmad library** and **Extra library dirs**
fields (Input tab, shown only when Tao is selected) are optional overrides for the
cases where auto-discovery doesn't work — most commonly the
[standalone executable](https://github.com/randy-afk/ranoptics3d/releases), which has
no way to find a Bmad install on your machine and always needs this set explicitly.

- **Bmad library**: full path to `libtao.so` (Linux), `libtao.dylib` (macOS), or
  `libtao.dll` (Windows).
- **Extra library dirs**: comma-separated directories to search for Bmad's own
  dependencies (GSL, LAPACK, FFTW3, HDF5, ...), if they aren't already sitting next
  to `libtao.*` itself.

Both fields save automatically and are remembered across launches — set them once.

**Finding your library**, if you don't already know the path: for a conda-forge
Bmad install, it's under your environment's `lib/` directory —

```bash
find "$CONDA_PREFIX/lib" -maxdepth 1 -name "libtao*"
```

If Bmad was built from source, check `$ACC_ROOT_DIR` instead:

```bash
find "$ACC_ROOT_DIR" -name "libtao*" 2>/dev/null
```

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
