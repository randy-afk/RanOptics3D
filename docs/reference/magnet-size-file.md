# Magnet Size File

The magnet size file lets you override the default element box dimensions on a
per-pattern basis. Load it from the **Beam & Inspector** tab in the GUI before rendering.

---

## Format

```
# name      shape      outer_x(cm)   outer_y(cm)
MQA*        cylinder   10.0          10.0
MQB*        block      8.0           12.0
QF          block      8.0
```

Lines starting with `#` are comments and are ignored.

---

## Fields

| Field | Description |
|---|---|
| `name` | Element name pattern — wildcards `*` and `?` supported |
| `shape` | `cylinder` or `block` (default: `block`) |
| `outer_x` | Horizontal half-width in cm (default: `element_half_width × 100`) |
| `outer_y` | Vertical half-height in cm (default: same as `outer_x` if omitted) |

---

## Notes

!!! note
    Patterns are matched in order — the first matching pattern wins.
    Put more specific patterns before broader wildcards.

!!! tip
    Use `cylinder` for circular-aperture magnets (solenoids, round-bore quads)
    and `block` for rectangular cross-section elements.
