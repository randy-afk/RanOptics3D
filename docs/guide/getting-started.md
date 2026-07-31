# Getting Started

## Installation

No installation required. Run directly from the repository.

### Dependencies

```bash
pip install plotly numpy PySide6
```

For Tao/Bmad backend:

```bash
pip install pytao
```

---

## Running the App

From the `pkg/` directory:

```bash
python -m ranoptics3d
# or
python RanOptics3D.py
```

---

## Basic Workflow

1. Launch the GUI.
2. Select your simulation code from the **Input** tab.
3. Point to your input file (see [Supported Backends](../reference/backends.md) for file types).
4. Set your output directory.
5. Click **▶ Render 3D**.

The output is a single HTML file — open it in any modern browser. By
default it loads Plotly.js from a CDN (small file, needs internet on
first view); check **Fully self-contained HTML** in the GUI or pass
`--offline` on the CLI to embed Plotly.js instead, for a larger file that
works with no internet connection at all. No server is required either way.

---

!!! tip "First time?"
    Render with default settings first to confirm the lattice loads correctly.
    Open the HTML, hit **Iso** for an overview, then click an element to verify
    the Selected Element panel populates. From there, explore the Beam & Inspector
    tab to enable the σ tube and configure the Twiss Inspector.
