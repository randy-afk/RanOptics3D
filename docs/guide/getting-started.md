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

The output is a self-contained HTML file — open it in any modern browser.
No internet connection or server required.

---

!!! tip "First time?"
    Render with default settings first to confirm the lattice loads correctly.
    Open the HTML, hit **Iso** for an overview, then click an element to verify
    the Selected Element panel populates. From there, explore the Beam & Inspector
    tab to enable the σ tube and configure the Twiss Inspector.
