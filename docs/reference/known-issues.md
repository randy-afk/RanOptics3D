# Known Issues

---

## Short Solenoids — Donut Geometry

**Symptom:** Solenoids shorter than ~0.5 m render as a donut shape rather than a
helix coil, because the element has less than one full turn at the default coil pitch.

**Status:** Pinned for a future release.

**Workaround:** The element is still fully clickable and all attributes are correct —
only the visual geometry is affected.

---

## Twiss Inspector — Optics Plot Spikes (specific ELEGANT lattices)

**Symptom:** The Twiss Inspector optics popup shows incorrect data (large spikes)
for some specific ELEGANT lattices. Other lattices are unaffected.

**Status:** Under investigation. Likely an element-ordering issue in the affected run.

**Workaround:** Use [RanOptics](https://github.com/randy-afk/ranoptics) (2D) for
optics inspection on the affected lattice in the meantime.

---

!!! tip "Reporting issues"
    Open an issue on the [GitHub repository](https://github.com/randy-afk/RanOptics3D)
    with your backend, lattice file type, and a description of the problem.
