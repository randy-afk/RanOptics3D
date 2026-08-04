"""
ranoptics3d._theme
===================
Color palette and fonts, kept in sync with RanOptics's core/themes.py so
the two tools present a consistent look. Supports dark (default) and
light themes via apply_theme(mode), mirroring RanOptics's own switcher.
"""
try:
    from PySide6.QtGui import QFont, QColor, QPalette
except ImportError:
    QFont = QColor = QPalette = None

# ── Theme palettes ────────────────────────────────────────────────────────────
_DARK = dict(
    BG       = "#0e130f",   # Main background
    MANTLE   = "#0a0e0b",   # Header / chrome
    CRUST    = "#0a0e0b",   # Menubar / status bar
    PANEL    = "#141b15",   # Card / panel surface
    PANEL2   = "#1a221b",   # Slightly lighter panel
    SURFACE2 = "#222e24",   # Hover state
    BORDER   = "#2a382c",   # Borders and dividers
    FG       = "#e7eee8",   # Primary text
    FG_DIM   = "#95a797",   # Dimmed / hint text
    FG_LBL   = "#65786a",   # Label / faint text
    ACCENT   = "#46cd8a",   # Emerald green — primary accent
    ACCENTH  = "#5ed99b",   # Accent hover
    AINK     = "#05140c",   # Text on accent bg
    ASOFT    = "rgba(70,205,138,.13)",  # Soft accent bg
    COPPER   = "#d98a5c",   # Copper — secondary accent
    CSOFT    = "rgba(217,138,92,.14)",  # Soft copper bg
    ERROR    = "#e0705f",   # Danger / error
    WARN     = "#d98a5c",   # Warning (copper)
    RAN_CLR  = "#46cd8a",   # Brand green (same as ACCENT in new theme)
    SHADOW   = "0 8px 30px rgba(0,0,0,.45)",
)

_LIGHT = dict(
    BG       = "#e9efe7",
    MANTLE   = "#dde6db",
    CRUST    = "#dde6db",
    PANEL    = "#ffffff",
    PANEL2   = "#f4f8f3",
    SURFACE2 = "#e1e9df",
    BORDER   = "#cfdace",
    FG       = "#15201a",
    FG_DIM   = "#566656",
    FG_LBL   = "#859786",
    ACCENT   = "#11955f",
    ACCENTH  = "#0e7f51",
    AINK     = "#ffffff",
    ASOFT    = "rgba(17,149,95,.10)",
    COPPER   = "#b1623a",
    CSOFT    = "rgba(177,98,58,.12)",
    ERROR    = "#c4503e",
    WARN     = "#b1623a",
    RAN_CLR  = "#11955f",
    SHADOW   = "0 8px 30px rgba(60,80,60,.16)",
)

# Current theme mode
_current_mode = "dark"

def _load(palette):
    """Inject palette into module globals and set up aliases."""
    import sys
    m = sys.modules[__name__]
    for k, v in palette.items():
        setattr(m, k, v)
    # Keep aliases in sync (matches RanOptics's own alias scheme)
    m.ACCENT2    = m.ACCENT
    m.PEACH      = m.ACCENT
    m.HIGHLIGHT  = m.WARN
    m.SUCCESS    = m.RAN_CLR

def apply_theme(mode="dark"):
    """Switch between 'dark' and 'light' themes. Call from GUI."""
    import sys
    m = sys.modules[__name__]
    m._current_mode = mode
    _load(_DARK if mode == "dark" else _LIGHT)

def apply_qpalette(app):
    """Apply the current theme's colors to a QApplication's QPalette —
    affects native/unstyled Qt chrome (tooltips, etc.) that the app's own
    inline stylesheets don't cover. Reads whatever apply_theme() last set.
    """
    import sys
    m = sys.modules[__name__]
    pal = QPalette()
    for role, col in [
        (QPalette.Window, m.BG), (QPalette.WindowText, m.FG),
        (QPalette.Base, m.PANEL), (QPalette.AlternateBase, m.BG),
        (QPalette.Text, m.FG), (QPalette.Button, m.PANEL),
        (QPalette.ButtonText, m.FG), (QPalette.Highlight, m.ACCENT),
        (QPalette.HighlightedText, m.FG), (QPalette.PlaceholderText, m.FG_DIM),
    ]:
        pal.setColor(role, QColor(col))
    app.setPalette(pal)

# ── Fonts ─────────────────────────────────────────────────────────────────────

def build_gui_fonts():
    FONT_MAIN  = QFont("IBM Plex Sans"); FONT_MAIN.setPointSize(11)
    FONT_BOLD  = QFont("IBM Plex Sans"); FONT_BOLD.setPointSize(11); FONT_BOLD.setBold(True)
    FONT_SMALL = QFont("IBM Plex Sans"); FONT_SMALL.setPointSize(9)
    FONT_MONO  = QFont("IBM Plex Mono"); FONT_MONO.setPointSize(10)
    FONT_HDR   = QFont("IBM Plex Sans"); FONT_HDR.setPointSize(18); FONT_HDR.setBold(True)
    FONT_SEC   = QFont("IBM Plex Sans"); FONT_SEC.setPointSize(11); FONT_SEC.setBold(True)
    return FONT_MAIN, FONT_BOLD, FONT_SMALL, FONT_MONO, FONT_HDR, FONT_SEC

# ── Load dark theme by default ────────────────────────────────────────────────
apply_theme("dark")
