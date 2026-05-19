"""
ranoptics3d._gui
================
PySide6 GUI — RanOptics3DGUI main window, all widgets and layout.
"""
from __future__ import annotations
import threading
from pathlib import Path

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
        QLineEdit, QCheckBox, QComboBox, QTabWidget, QScrollArea,
        QTextEdit, QProgressBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
        QInputDialog, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import (
        QFont, QColor, QPalette, QAction, QPainter, QPen, QTextCharFormat,
    )
    _HAVE_PYSIDE = True
except ImportError:
    _HAVE_PYSIDE = False

from ._plot import plot_optics_3d, compute_lattice_stats
from ._backends import load_tao, load_elegant, load_xsuite, load_madx
from ._backends.tao import _parse_tao_init
from ._plot import _parse_camera_eye

# ════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════
#  SECTION 4 — PySide6 GUI
# ════════════════════════════════════════════════════════════════════════════


try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
        QLineEdit, QCheckBox, QComboBox, QTabWidget, QScrollArea,
        QTextEdit, QProgressBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
        QInputDialog, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import (
        QFont, QColor, QPalette, QAction, QPainter, QPen, QTextCharFormat,
    )
    _HAVE_PYSIDE = True
except ImportError:
    _HAVE_PYSIDE = False


# ── RanOptics palette (matches ranoptics.py exactly) ──────────────────────────
BG       = "#2C5446"
MANTLE   = "#234038"
CRUST    = "#1a2f28"
PANEL    = "#3D6B5C"
SURFACE2 = "#4A7D6C"
BORDER   = "#5A8A78"
FG       = "#EEF5F2"
FG_DIM   = "#A8C4BC"
FG_LBL   = "#8AB0A6"
ACCENT   = "#FDA769"
RAN_CLR  = "#00e676"
ERROR    = "#d62828"
ACCENT2  = "#FDA769"
WARN     = "#FEC868"
SUCCESS  = "#00e676"
TEAL     = "#FEC868"


def _build_gui_fonts():
    FONT_MAIN  = QFont(); FONT_MAIN.setPointSize(11)
    FONT_BOLD  = QFont(); FONT_BOLD.setPointSize(11);  FONT_BOLD.setBold(True)
    FONT_SMALL = QFont(); FONT_SMALL.setPointSize(11)
    FONT_MONO  = QFont("Monospace"); FONT_MONO.setPointSize(10)
    FONT_HDR   = QFont("Monospace"); FONT_HDR.setPointSize(16);  FONT_HDR.setBold(True)
    FONT_SEC   = QFont(); FONT_SEC.setPointSize(11);  FONT_SEC.setBold(True)
    return FONT_MAIN, FONT_BOLD, FONT_SMALL, FONT_MONO, FONT_HDR, FONT_SEC


# Stylesheet snippets (initialised at GUI startup)
def _build_stylesheets():
    return {
        'entry': f"""
            QLineEdit {{
                background: {MANTLE}; border: 1px solid {BORDER};
                border-radius: 8px; color: {FG}; padding: 4px 10px;
                selection-background-color: {ACCENT}; selection-color: {CRUST};
            }}
            QLineEdit:focus {{
                border-color: {ACCENT}; border-left: 3px solid {ACCENT};
                background: {BG};
            }}
            QLineEdit[readOnly="true"] {{ color: {FG_DIM}; background: {PANEL}; }}
        """,
        'combo': f"""
            QComboBox {{
                background: {MANTLE}; border: 1px solid {BORDER};
                border-radius: 8px; color: {FG}; padding: 4px 10px;
            }}
            QComboBox:focus {{ border-color: {ACCENT}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ width: 0; height: 0; }}
            QComboBox QAbstractItemView {{
                background: {PANEL}; color: {FG}; border: 1px solid {BORDER};
                border-radius: 6px; padding: 2px;
                selection-background-color: {ACCENT}; selection-color: {CRUST};
                outline: none;
            }}
        """,
        'btn': f"""
            QPushButton {{
                background: {PANEL}; border: 1px solid {BORDER};
                border-radius: 8px; color: {ACCENT}; padding: 4px 10px;
                font-weight: 500;
            }}
            QPushButton:hover  {{
                background: {SURFACE2}; border-color: {ACCENT}; color: {ACCENT};
            }}
            QPushButton:pressed {{ background: {BORDER}; }}
            QPushButton:disabled {{ color: {FG_DIM}; border-color: {BORDER}; background: {PANEL}; }}
        """,
        'chk': f"""
            QCheckBox {{ color: {FG}; spacing: 7px; }}
            QCheckBox::indicator {{
                width: 15px; height: 15px; border-radius: 4px;
                border: 1px solid {SURFACE2}; background: {MANTLE};
            }}
            QCheckBox::indicator:unchecked:hover {{ border-color: {ACCENT}; }}
            QCheckBox::indicator:checked {{
                background: {ACCENT}; border-color: {ACCENT};
            }}
        """,
        'tab': f"""
            QTabWidget::pane {{
                background: {PANEL}; border: 1px solid {BORDER};
                border-radius: 10px; top: -1px;
            }}
            QTabBar::tab {{
                background: {MANTLE}; color: {FG_LBL}; padding: 7px 20px;
                border: 1px solid {BORDER}; border-bottom: none; margin-right: 3px;
                border-top-left-radius: 8px; border-top-right-radius: 8px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {PANEL}; color: {ACCENT};
                border-bottom-color: {PANEL};
            }}
            QTabBar::tab:hover:!selected {{ background: {SURFACE2}; color: {FG}; }}
        """,
        'scroll': f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {MANTLE}; width: 6px; margin: 0; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {SURFACE2}; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """,
    }


# ── 3D logo widget ────────────────────────────────────────────────────────────

if _HAVE_PYSIDE:
    class _Cube3DLogo(QWidget):
        """Small isometric cube + axes — 3D analogue of the FODO logo."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setFixedSize(108, 64)

        def paintEvent(self, event):
            from PySide6.QtCore import QPointF
            p = QPainter(self)
            p.setRenderHint(QPainter.Antialiasing)
            cx, cy = 54, 36
            s = 16  # half-size
            # Isometric projection: x' = (x-y)*cos30, y' = (x+y)*sin30 - z
            def iso(x, y, z):
                import math
                c30 = math.cos(math.radians(30))
                s30 = math.sin(math.radians(30))
                return QPointF(cx + (x - y) * c30 * s,
                               cy + (x + y) * s30 * s - z * s)
            # Draw three visible faces of a unit cube
            top = [iso(0, 0, 1), iso(1, 0, 1), iso(1, 1, 1), iso(0, 1, 1)]
            right = [iso(1, 0, 0), iso(1, 1, 0), iso(1, 1, 1), iso(1, 0, 1)]
            front = [iso(0, 0, 0), iso(1, 0, 0), iso(1, 0, 1), iso(0, 0, 1)]
            from PySide6.QtGui import QBrush, QPolygonF
            for face, color in [(top, "#1f77b4"),
                                (right, "#d62728"),
                                (front, "#2ca02c")]:
                poly = QPolygonF(face)
                p.setBrush(QBrush(QColor(color)))
                p.setPen(QPen(QColor("#ffffff"), 1.2))
                p.drawPolygon(poly)
            # Mini X/Y/Z axes at lower-left
            ox, oy = 8, 56
            ax_len = 14
            pen = QPen(QColor("#ff5555"), 2); p.setPen(pen)
            p.drawLine(QPointF(ox, oy), QPointF(ox + ax_len, oy))
            pen = QPen(QColor("#55ff55"), 2); p.setPen(pen)
            p.drawLine(QPointF(ox, oy), QPointF(ox, oy - ax_len))
            pen = QPen(QColor("#5599ff"), 2); p.setPen(pen)
            p.drawLine(QPointF(ox, oy), QPointF(ox - 8, oy + 4))


# ── GUI helpers ───────────────────────────────────────────────────────────────

def _make_scroll_widget(scroll_ss):
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setStyleSheet(scroll_ss)
    inner = QWidget(); inner.setStyleSheet("background: transparent;")
    vbox = QVBoxLayout(inner)
    vbox.setContentsMargins(0, 4, 0, 8); vbox.setSpacing(0)
    sa.setWidget(inner)
    return sa, inner, vbox


def _sec(layout, title, FONT_SEC):
    w = QWidget(); h = QHBoxLayout(w)
    h.setContentsMargins(8, 8, 8, 2); h.setSpacing(8)
    lbl = QLabel(f"  {title.upper()}  "); lbl.setFont(FONT_SEC)
    lbl.setStyleSheet(f"color: {CRUST}; background: {ACCENT2}; "
                      f"border-radius: 4px; padding: 1px 4px;")
    line = QFrame(); line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {BORDER}; background: {BORDER};")
    h.addWidget(lbl); h.addWidget(line, 1)
    layout.addWidget(w)


def _row(layout):
    w = QWidget(); w.setStyleSheet("background: transparent;")
    h = QHBoxLayout(w); h.setContentsMargins(8, 2, 8, 2); h.setSpacing(6)
    h.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(w)
    return h


def _lbl(layout, text, FONT_MAIN, width=160):
    lbl = QLabel(text); lbl.setFont(FONT_MAIN)
    lbl.setStyleSheet(f"color: {FG_LBL}; background: transparent;")
    lbl.setFixedWidth(width); lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    layout.addWidget(lbl)


def _ent(layout, FONT_MONO, entry_ss, width=200, placeholder=""):
    e = QLineEdit(); e.setFont(FONT_MONO)
    e.setPlaceholderText(placeholder); e.setFixedWidth(width)
    e.setStyleSheet(entry_ss)
    layout.addWidget(e); return e


def _btn(layout, text, cmd, FONT_MAIN, width=80, color=ACCENT):
    b = QPushButton(text); b.setFont(FONT_MAIN); b.setFixedWidth(width)
    b.clicked.connect(cmd)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {PANEL}; border: 1px solid {BORDER};
            border-radius: 8px; color: {color}; padding: 4px 8px;
        }}
        QPushButton:hover {{ background: {SURFACE2}; border-color: {color}; }}
        QPushButton:pressed {{ background: {BORDER}; }}
        QPushButton:disabled {{ color: {FG_DIM}; border-color: {BORDER}; background: {PANEL}; }}
    """)
    layout.addWidget(b); return b


def _chk(layout, text, FONT_MAIN, chk_ss):
    c = QCheckBox(text); c.setFont(FONT_MAIN); c.setStyleSheet(chk_ss)
    layout.addWidget(c); return c


def _dd(layout, items, FONT_MAIN, combo_ss, width=120):
    cb = QComboBox(); cb.setFont(FONT_MAIN); cb.addItems(items)
    cb.setFixedWidth(width); cb.setStyleSheet(combo_ss)
    layout.addWidget(cb); return cb


def _hint(layout, text, FONT_SMALL):
    lbl = QLabel(text); lbl.setFont(FONT_SMALL)
    lbl.setStyleSheet(f"color: {FG_DIM}; background: transparent;")
    layout.addWidget(lbl)


def _help(layout, text, FONT_SMALL):
    lbl = QLabel(text); lbl.setFont(FONT_SMALL); lbl.setWordWrap(True)
    lbl.setStyleSheet(f"color: {FG_DIM}; background: transparent; "
                      f"padding: 0 12px 4px 12px;")
    layout.addWidget(lbl)


def _clf(line):
    lo = line.lower()
    if any(w in lo for w in ("error", "traceback", "exception", "failed", "✗")):
        return "error"
    if any(w in lo for w in ("warning", "warn")):
        return "warn"
    if any(w in lo for w in ("saved", "done", "complete", "✓")):
        return "ok"
    return "info"


# ════════════════════════════════════════════════════════════════════════════
#  Main GUI window
# ════════════════════════════════════════════════════════════════════════════

if _HAVE_PYSIDE:

    class RanOptics3DGUI(QMainWindow):
        _sig_log      = Signal(str, str)
        _sig_done     = Signal(str)
        _sig_finally  = Signal()

        _RECENT_FILE = Path.home() / ".ranoptics3d_recent.json"
        _PRESET_FILE = Path.home() / ".ranoptics3d_presets.json"
        _MAX_RECENT  = 8

        # The element legend names the GUI exposes as visibility toggles
        _ELEMENT_TYPE_NAMES = ('Dipole', 'Quadrupole', 'Sextupole', 'Octupole',
                               'Kicker', 'Monitor', 'RF Cavity', 'Solenoid', 'Marker')

        def __init__(self):
            super().__init__()
            self.setWindowTitle("RanOptics3D — 3D Lattice Layout Viewer")
            self.resize(1280, 960); self.setMinimumSize(1000, 800)
            self.setStyleSheet(f"""
                QMainWindow {{ background: {BG}; }}
                QWidget {{ background: {BG}; }}
                QToolTip {{
                    background: {PANEL}; color: {FG};
                    border: 1px solid {BORDER}; border-radius: 6px;
                    padding: 4px 8px;
                }}
            """)

            (self.FONT_MAIN, self.FONT_BOLD, self.FONT_SMALL, self.FONT_MONO,
             self.FONT_HDR, self.FONT_SEC) = _build_gui_fonts()
            self.SS = _build_stylesheets()

            self._last_output = None
            self._uni_checks = {}
            self._uni_label_edits = {}
            self._uni_n = 1
            self._type_visible = {n: True for n in self._ELEMENT_TYPE_NAMES}
            self._type_opacity = {}

            central = QWidget(); self.setCentralWidget(central)
            self._root_layout = QVBoxLayout(central)
            self._root_layout.setContentsMargins(0, 0, 0, 0)
            self._root_layout.setSpacing(0)

            self._build_menubar()
            self._build_header()
            self._build_form()
            self._build_run_bar()
            self._build_log()
            self._build_statusbar()

            self._sig_log.connect(self._log)
            self._sig_done.connect(self._on_run_done)
            self._sig_finally.connect(self._on_run_finally)

            self._refresh_recent_menu()
            self._refresh_preset_menu()

        # ── Menu bar ──────────────────────────────────────────────────────────

        def _build_menubar(self):
            mb = self.menuBar()
            mb.setStyleSheet(f"""
                QMenuBar {{
                    background: {CRUST}; color: {FG_LBL};
                    border-bottom: 1px solid {BORDER};
                }}
                QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
                QMenuBar::item:selected {{ background: {SURFACE2}; color: {FG}; }}
                QMenu {{
                    background: {MANTLE}; color: {FG};
                    border: 1px solid {BORDER}; border-radius: 8px;
                    padding: 4px;
                }}
                QMenu::item {{ padding: 5px 20px; border-radius: 4px; }}
                QMenu::item:selected {{ background: {PANEL}; color: {ACCENT}; }}
                QMenu::separator {{ background: {BORDER}; height: 1px; margin: 4px 8px; }}
            """)
            fm = mb.addMenu("File")
            fm.addAction(QAction("Browse Input…", self, triggered=self._browse_input))
            fm.addAction(QAction("Save Output As…", self, triggered=self._browse_output))
            fm.addSeparator()
            self._recent_menu = fm.addMenu("Recent Files")
            fm.addSeparator()
            fm.addAction(QAction("Copy Output Path", self, triggered=self._copy_path))

            pm = mb.addMenu("Presets")
            pm.addAction(QAction("Save Current as Preset…", self,
                                 triggered=self._preset_save_dialog))
            pm.addSeparator()
            self._preset_menu = pm.addMenu("Load Preset")
            pm.addAction(QAction("Delete a preset…", self,
                                 triggered=self._preset_delete_dialog))

            rm = mb.addMenu("Run")
            rm.addAction(QAction("▶ Run", self, triggered=self._run))
            rm.addAction(QAction("🔍 Inspect lattice", self,
                                 triggered=self._dry_run))

        # ── Header ────────────────────────────────────────────────────────────

        def _build_header(self):
            h = QWidget(); h.setFixedHeight(64)
            h.setStyleSheet(f"background: {MANTLE}; "
                            f"border-bottom: 2px solid {BORDER};")
            row = QHBoxLayout(h); row.setContentsMargins(16, 0, 20, 0); row.setSpacing(8)
            row.addWidget(_Cube3DLogo())

            txt = QWidget(); txt.setStyleSheet("background: transparent;")
            tv = QVBoxLayout(txt); tv.setContentsMargins(6, 8, 0, 8); tv.setSpacing(2)
            name_lbl = QLabel(
                f'<span style="color:{RAN_CLR};letter-spacing:2px;">Ran</span>'
                f'<span style="color:{ERROR};letter-spacing:2px;">Optics</span>'
                f'<span style="color:{ACCENT};letter-spacing:2px;">3D</span>'
            )
            name_lbl.setFont(self.FONT_HDR)
            name_lbl.setStyleSheet("background: transparent;")
            tv.addWidget(name_lbl)
            sub = QLabel("3D Lattice Layout Viewer  •  v1.0.0")
            sub.setFont(self.FONT_SMALL)
            sub.setStyleSheet(f"color: {FG_DIM}; background: transparent;")
            tv.addWidget(sub)
            row.addWidget(txt); row.addStretch()

            rf = QWidget(); rf.setStyleSheet("background: transparent;")
            rv = QVBoxLayout(rf); rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(2)
            for t in ("Author: Randika Gamage (randika@jlab.org)",
                      "Support: Good luck, I believe in you"):
                l = QLabel(t); l.setFont(self.FONT_SMALL); l.setAlignment(Qt.AlignLeft)
                l.setStyleSheet(f"color: {FG_DIM}; background: transparent;")
                rv.addWidget(l)
            row.addWidget(rf)
            self._root_layout.addWidget(h)

        # ── Status bar ────────────────────────────────────────────────────────

        def _build_statusbar(self):
            sb = QWidget(); sb.setFixedHeight(28)
            sb.setStyleSheet(f"background: {MANTLE}; border-top: 1px solid {BORDER};")
            row = QHBoxLayout(sb); row.setContentsMargins(12, 0, 8, 0); row.setSpacing(8)
            self._status_lbl = QLabel("Idle"); self._status_lbl.setFont(self.FONT_SMALL)
            self._status_lbl.setStyleSheet(f"color: {FG_DIM}; background: transparent;")
            row.addWidget(self._status_lbl); row.addStretch()
            self._stats_lbl = QLabel(""); self._stats_lbl.setFont(self.FONT_SMALL)
            self._stats_lbl.setStyleSheet(f"color: {FG_DIM}; background: transparent;")
            row.addWidget(self._stats_lbl)
            self._root_layout.addWidget(sb)

        def _set_status(self, text):
            self._status_lbl.setText(text)

        def _set_stats(self, text):
            self._stats_lbl.setText(text)

        # ── Run bar ───────────────────────────────────────────────────────────

        def _build_run_bar(self):
            bar = QWidget(); bar.setFixedHeight(52)
            bar.setStyleSheet(f"background: {MANTLE}; border-top: 1px solid {BORDER};")
            row = QHBoxLayout(bar); row.setContentsMargins(12, 6, 12, 6); row.setSpacing(6)

            self.run_btn = QPushButton("▶  Render 3D"); self.run_btn.setFont(self.FONT_BOLD)
            self.run_btn.setFixedSize(130, 36); self.run_btn.clicked.connect(self._run)
            self.run_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {ACCENT}; border-radius: 8px;
                    color: {CRUST}; font-weight: bold; border: none;
                }}
                QPushButton:hover {{ background: {TEAL}; color: {CRUST}; }}
                QPushButton:disabled {{ background: {BORDER}; color: {FG_DIM}; border: none; }}
            """)
            row.addWidget(self.run_btn)

            def _action_btn(text, cmd, color, width=130):
                b = QPushButton(text); b.setFont(self.FONT_BOLD)
                b.setFixedSize(width, 36); b.clicked.connect(cmd)
                b.setStyleSheet(f"""
                    QPushButton {{
                        background: {PANEL}; border: 1px solid {color};
                        border-radius: 8px; color: {color}; font-weight: 500;
                    }}
                    QPushButton:hover {{ background: {color}; color: {CRUST}; }}
                    QPushButton:disabled {{ color: {FG_DIM}; border-color: {BORDER}; background: {PANEL}; }}
                """)
                row.addWidget(b); return b

            self.open_btn = _action_btn("🌐  Open in browser", self._open_plot, SUCCESS, 160)
            self.dryrun_btn = _action_btn("🔍  Inspect", self._dry_run, ACCENT2, 110)
            self.open_btn.setEnabled(False)
            row.addStretch()

            clr = QPushButton("⊗  Clear log"); clr.setFont(self.FONT_MAIN)
            clr.setFixedSize(115, 36); clr.clicked.connect(self._clear_log)
            clr.setStyleSheet(f"""
                QPushButton {{
                    background: {MANTLE}; border: 1px solid {BORDER};
                    border-radius: 8px; color: {FG_LBL};
                }}
                QPushButton:hover {{ background: {SURFACE2}; color: {FG}; border-color: {ACCENT2}; }}
            """)
            row.addWidget(clr)
            self._root_layout.addWidget(bar)

        # ── Log ───────────────────────────────────────────────────────────────

        def _build_log(self):
            lf = QWidget(); lf.setStyleSheet(f"background: {BG};")
            lv = QVBoxLayout(lf); lv.setContentsMargins(12, 4, 12, 4); lv.setSpacing(2)
            hdr = QLabel("OUTPUT LOG"); hdr.setFont(self.FONT_SEC)
            hdr.setStyleSheet(f"color: {ACCENT2}; background: transparent;")
            lv.addWidget(hdr)
            self.log = QTextEdit(); self.log.setReadOnly(True)
            self.log.setFont(self.FONT_MONO); self.log.setFixedHeight(140)
            self.log.setStyleSheet(f"""
                QTextEdit {{
                    background: {MANTLE}; color: {FG};
                    border: 1px solid {BORDER}; border-radius: 8px;
                    padding: 6px; selection-background-color: {ACCENT};
                }}
            """)
            lv.addWidget(self.log)
            self._root_layout.addWidget(lf)
            self._log("Ready. Configure options above and click ▶ Render 3D.\n", "dim")

        # ── Form ──────────────────────────────────────────────────────────────

        def _build_form(self):
            outer = QWidget(); outer.setStyleSheet(f"background: {BG};")
            outer_h = QHBoxLayout(outer); outer_h.setContentsMargins(8, 4, 8, 0)
            outer_h.setSpacing(8)

            self._tab_l = QTabWidget(); self._tab_l.setStyleSheet(self.SS['tab'])
            self._tab_l.setFont(self.FONT_SEC)
            self._tab_r = QTabWidget(); self._tab_r.setStyleSheet(self.SS['tab'])
            self._tab_r.setFont(self.FONT_SEC)

            for name in ("Input", "Range & Universes", "Beam & Inspector"):
                self._tab_l.addTab(QWidget(), name)
            for name in ("3D View", "Elements", "Overlays"):
                self._tab_r.addTab(QWidget(), name)

            def _scroll_tab(tab_widget, idx):
                w = tab_widget.widget(idx)
                sa, inner, vbox = _make_scroll_widget(self.SS['scroll'])
                vbox.addStretch()
                layout = QVBoxLayout(w); layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(sa)
                return vbox

            self._input_layout   = _scroll_tab(self._tab_l, 0)
            self._range_layout   = _scroll_tab(self._tab_l, 1)
            self._beam_layout    = _scroll_tab(self._tab_l, 2)
            self._view_layout    = _scroll_tab(self._tab_r, 0)
            self._elements_layout= _scroll_tab(self._tab_r, 1)
            self._overlays_layout= _scroll_tab(self._tab_r, 2)

            outer_h.addWidget(self._tab_l, 1)
            outer_h.addWidget(self._tab_r, 1)
            self._root_layout.addWidget(outer, 1)

            for lay in (self._input_layout, self._range_layout, self._beam_layout,
                        self._view_layout, self._elements_layout, self._overlays_layout):
                lay.takeAt(lay.count() - 1)

            self._build_input_section(self._input_layout)
            self._build_range_section(self._range_layout)
            self._build_beam_section(self._beam_layout)
            self._build_view_section(self._view_layout)
            self._build_elements_section(self._elements_layout)
            self._build_overlays_section(self._overlays_layout)

            for lay in (self._input_layout, self._range_layout, self._beam_layout,
                        self._view_layout, self._elements_layout, self._overlays_layout):
                lay.addStretch(1)

        # ── Input section ─────────────────────────────────────────────────────

        def _build_input_section(self, layout):
            r = _row(layout); _lbl(r, "Input file  *", self.FONT_MAIN)
            self.w_input = _ent(r, self.FONT_MONO, self.SS['entry'],
                                width=220,
                                placeholder="tao.init / run.ele / lattice.json / twiss.tfs")
            self.w_input.textChanged.connect(lambda t: self._on_input_change(t.strip()))
            _btn(r, "Browse", self._browse_input, self.FONT_MAIN, width=70)
            _help(layout,
                  "Auto-detected from extension: .init=Tao, .ele=ELEGANT, "
                  ".json=xsuite, .tfs=MAD-X.", self.FONT_SMALL)

            r = _row(layout); _lbl(r, "Code backend", self.FONT_MAIN)
            self.w_code = _dd(r, ["tao", "elegant", "xsuite", "madx"],
                              self.FONT_MAIN, self.SS['combo'], width=110)
            self.w_code.currentTextChanged.connect(
                lambda _: (self._update_xsuite_rows(), self._update_madx_rows()))

            self._xsuite_widget = QWidget()
            self._xsuite_widget.setStyleSheet("background: transparent;")
            xv = QVBoxLayout(self._xsuite_widget)
            xv.setContentsMargins(0, 0, 0, 0); xv.setSpacing(0)
            rl = _row(xv); _lbl(rl, "xsuite line name", self.FONT_MAIN)
            self.w_xsuite_line = _ent(rl, self.FONT_MONO, self.SS['entry'],
                                       width=160,
                                       placeholder="auto-detect if blank")
            layout.addWidget(self._xsuite_widget)
            self._xsuite_widget.hide()

            self._madx_widget = QWidget()
            self._madx_widget.setStyleSheet("background: transparent;")
            mv = QVBoxLayout(self._madx_widget)
            mv.setContentsMargins(0, 0, 0, 0); mv.setSpacing(0)
            rm = _row(mv); _lbl(rm, "Survey file (.tfs)", self.FONT_MAIN)
            self.w_madx_survey = _ent(rm, self.FONT_MONO, self.SS['entry'],
                                       width=200,
                                       placeholder="optional — for floor plan")
            _btn(rm, "Browse", self._browse_madx_survey, self.FONT_MAIN, width=70)
            _help(mv, "MAD-X SURVEY output. Required for proper 3D layout.",
                  self.FONT_SMALL)
            layout.addWidget(self._madx_widget)
            self._madx_widget.hide()

            r = _row(layout); _lbl(r, "Output HTML", self.FONT_MAIN)
            self.w_output = _ent(r, self.FONT_MONO, self.SS['entry'], width=180)
            self.w_output.setText("optics3d.html")
            _btn(r, "Save as", self._browse_output, self.FONT_MAIN, width=70)
            _help(layout, "Output HTML file. Open in any browser to view 3D scene.",
                  self.FONT_SMALL)

            r = _row(layout); _lbl(r, "Plot title", self.FONT_MAIN)
            self.w_title = _ent(r, self.FONT_MONO, self.SS['entry'],
                                width=240, placeholder="optional")

        # ── Range / universes section ─────────────────────────────────────────

        def _build_range_section(self, layout):
            _sec(layout, "Range Filter", self.FONT_SEC)
            r = _row(layout); _lbl(r, "Range  START:END", self.FONT_MAIN)
            self.w_range = _ent(r, self.FONT_MONO, self.SS['entry'],
                                width=240,
                                placeholder="QUA01:QUA06  or  3.0:19.0")
            _help(layout,
                  "Sub-range to render. Use element names or s positions.",
                  self.FONT_SMALL)

            _sec(layout, "Universes (Tao multi-universe)", self.FONT_SEC)
            self._uni_widget = QWidget()
            self._uni_widget.setStyleSheet("background: transparent;")
            self._uni_vbox = QVBoxLayout(self._uni_widget)
            self._uni_vbox.setContentsMargins(0, 0, 0, 0); self._uni_vbox.setSpacing(2)
            self._uni_checks_widget = QWidget()
            self._uni_checks_widget.setStyleSheet("background: transparent;")
            self._uni_checks_v = QVBoxLayout(self._uni_checks_widget)
            self._uni_checks_v.setContentsMargins(8, 2, 8, 2); self._uni_checks_v.setSpacing(2)
            self._uni_vbox.addWidget(self._uni_checks_widget)
            _help(self._uni_vbox, "Uncheck to exclude. Edit labels as desired.",
                  self.FONT_SMALL)
            layout.addWidget(self._uni_widget)
            placeholder = QLabel("(Single-universe lattice — no selection needed)")
            placeholder.setFont(self.FONT_SMALL)
            placeholder.setStyleSheet(f"color: {FG_DIM}; padding: 4px 12px;")
            self._uni_checks_v.addWidget(placeholder)
            self._uni_placeholder = placeholder

        # ── 3D view section ───────────────────────────────────────────────────

        def _build_view_section(self, layout):
            _sec(layout, "Axis Aspect & Scale", self.FONT_SEC)
            r = _row(layout); _lbl(r, "Aspect mode", self.FONT_MAIN)
            self.w_aspect = _dd(r, ["data (real proportions)",
                                    "manual (X/Y/Z scale)",
                                    "cube (equal axes)"],
                                self.FONT_MAIN, self.SS['combo'], width=200)
            _help(layout,
                  "‘data’: preserves true proportions. ‘manual’: each axis is "
                  "shown at (extent × scale). Use scale=1 for real size, "
                  "scale<1 to compress, scale>1 to stretch. ‘cube’: force "
                  "equal axes (rarely useful).", self.FONT_SMALL)
            r = _row(layout); _lbl(r, "X scale", self.FONT_MAIN)
            self.w_scale_x = _ent(r, self.FONT_MONO, self.SS['entry'],
                                   width=70); self.w_scale_x.setText("1.0")
            _lbl(r, "Y scale", self.FONT_MAIN, width=70)
            self.w_scale_y = _ent(r, self.FONT_MONO, self.SS['entry'],
                                   width=70); self.w_scale_y.setText("1.0")
            _lbl(r, "Z scale", self.FONT_MAIN, width=70)
            self.w_scale_z = _ent(r, self.FONT_MONO, self.SS['entry'],
                                   width=70); self.w_scale_z.setText("1.0")
            _help(layout,
                  "Used only when aspect=‘manual’. Example: lattice is 10 m "
                  "wide × 80 m long → X=1, Z=0.5 displays it as if Z were 40 m, "
                  "compressing the long axis to half its real length.",
                  self.FONT_SMALL)

            _sec(layout, "Camera & Convention", self.FONT_SEC)
            r = _row(layout); _lbl(r, "Camera preset", self.FONT_MAIN)
            self.w_camera = _dd(r, ["iso", "top", "side", "front", "free"],
                                self.FONT_MAIN, self.SS['combo'], width=110)
            _help(layout,
                  "Initial view. The HTML viewer lets you free-rotate "
                  "regardless.", self.FONT_SMALL)
            r = _row(layout)
            self.w_z_up = _chk(r, "Z-up convention (default Y-up)",
                                self.FONT_MAIN, self.SS['chk'])
            _help(layout, "Y-up matches Bmad/pytao. Z-up matches MAD-X surveyors.",
                  self.FONT_SMALL)

            _sec(layout, "Focus & Pivot", self.FONT_SEC)
            r = _row(layout); _lbl(r, "Focus on element", self.FONT_MAIN)
            self.w_focus_elem = _ent(r, self.FONT_MONO, self.SS['entry'],
                                      width=180,
                                      placeholder="e.g. IP1 or QF12 (blank = none)")
            r = _row(layout); _lbl(r, "Focus radius (m)", self.FONT_MAIN)
            self.w_focus_radius = _ent(r, self.FONT_MONO, self.SS['entry'],
                                        width=80, placeholder="blank = no crop")
            _help(layout,
                  "Centers rotation pivot on the named element so dragging in "
                  "the browser orbits around it instead of the lattice center. "
                  "If a radius is given, also crops the view to that distance.",
                  self.FONT_SMALL)

            r = _row(layout); _lbl(r, "Camera eye  x,y,z", self.FONT_MAIN)
            self.w_camera_eye = _ent(r, self.FONT_MONO, self.SS['entry'],
                                      width=180,
                                      placeholder="e.g. 1.5,1.2,1.5 (blank = preset)")
            _help(layout,
                  "Override camera eye position. Hover the modebar in any "
                  "rendered HTML, drag to your preferred view, then read the "
                  "eye position from the toolbar tooltip and paste here for "
                  "exact reproducibility.", self.FONT_SMALL)

            _sec(layout, "Theme", self.FONT_SEC)
            r = _row(layout)
            self.w_dark = _chk(r, "Dark mode", self.FONT_MAIN, self.SS['chk'])
            self.w_dark.setChecked(True)
            r = _row(layout)
            self.w_show_gizmo = _chk(r, "Show XYZ axis gizmo at origin",
                                      self.FONT_MAIN, self.SS['chk'])
            self.w_show_gizmo.setChecked(True)
            r = _row(layout)
            self.w_control_panel = _chk(r, "Embed live control panel in HTML",
                                         self.FONT_MAIN, self.SS['chk'])
            self.w_control_panel.setChecked(True)
            _help(layout,
                  "Adds an in-browser panel for type visibility, click-to-"
                  "focus, aspect sliders, live annotations, and pinned info — "
                  "no re-render needed for these.", self.FONT_SMALL)

            _sec(layout, "Beampipe", self.FONT_SEC)
            r = _row(layout)
            self.w_show_pipe = _chk(r, "Show beampipe centerline",
                                     self.FONT_MAIN, self.SS['chk'])
            self.w_show_pipe.setChecked(True)
            r = _row(layout); _lbl(r, "Pipe color", self.FONT_MAIN)
            self.w_pipe_color = _ent(r, self.FONT_MONO, self.SS['entry'],
                                      width=100, placeholder="#888888")
            self.w_pipe_color.setText("#888888")
            _lbl(r, "Width", self.FONT_MAIN, width=60)
            self.w_pipe_width = _ent(r, self.FONT_MONO, self.SS['entry'], width=50)
            self.w_pipe_width.setText("2")

        # ── Elements section ──────────────────────────────────────────────────

        def _build_elements_section(self, layout):
            _sec(layout, "Element Box Size", self.FONT_SEC)
            r = _row(layout); _lbl(r, "Half-width (m)", self.FONT_MAIN)
            self.w_half_w = _ent(r, self.FONT_MONO, self.SS['entry'], width=80)
            self.w_half_w.setText("0.2")
            _hint(r, "transverse horizontal", self.FONT_SMALL)
            r = _row(layout); _lbl(r, "Half-height (m)", self.FONT_MAIN)
            self.w_half_h = _ent(r, self.FONT_MONO, self.SS['entry'], width=80)
            self.w_half_h.setText("0.2")
            _hint(r, "transverse vertical", self.FONT_SMALL)
            _help(layout,
                  "Box size in beam-frame transverse coordinates. Tune to taste — "
                  "smaller for tight lattices, larger for visibility.",
                  self.FONT_SMALL)

            _sec(layout, "Bend Smoothness", self.FONT_SEC)
            r = _row(layout); _lbl(r, "Segments per bend", self.FONT_MAIN)
            self.w_bend_seg = _ent(r, self.FONT_MONO, self.SS['entry'], width=60)
            self.w_bend_seg.setText("12")
            _help(layout,
                  "Higher = smoother arcs but more file size / render time.",
                  self.FONT_SMALL)

            _sec(layout, "Visibility & Opacity", self.FONT_SEC)
            self._type_chk_widgets = {}
            self._type_op_widgets = {}
            for tname in self._ELEMENT_TYPE_NAMES:
                r = _row(layout)
                cb = QCheckBox(tname); cb.setChecked(True); cb.setFont(self.FONT_MAIN)
                cb.setStyleSheet(self.SS['chk']); cb.setFixedWidth(160)
                r.addWidget(cb)
                op_lbl = QLabel("opacity:"); op_lbl.setFont(self.FONT_SMALL)
                op_lbl.setStyleSheet(f"color: {FG_DIM}; background: transparent;")
                r.addWidget(op_lbl)
                op_e = QLineEdit("1.0"); op_e.setFont(self.FONT_MONO)
                op_e.setFixedWidth(50); op_e.setStyleSheet(self.SS['entry'])
                r.addWidget(op_e)
                self._type_chk_widgets[tname] = cb
                self._type_op_widgets[tname] = op_e
            _help(layout, "Uncheck to hide a type. Opacity 0.0–1.0; partial values "
                          "fade elements (good for monitors/markers).",
                  self.FONT_SMALL)

            r = _row(layout)
            self.w_show_markers = _chk(r, "Include markers/monitors as boxes",
                                        self.FONT_MAIN, self.SS['chk'])
            _help(layout,
                  "Markers and monitors are zero-length — boxes for them are tiny. "
                  "Off by default.", self.FONT_SMALL)

            r = _row(layout)
            self.w_show_outlines = _chk(r, "Show element outlines",
                                         self.FONT_MAIN, self.SS['chk'])
            self.w_show_outlines.setChecked(True)
            _help(layout,
                  "White edge lines on elements. Turn off to hide segment "
                  "outlines on curved dipoles.", self.FONT_SMALL)

            _sec(layout, "Mirror", self.FONT_SEC)
            r = _row(layout)
            self.w_flip_bend = _chk(r, "Flip bend direction (mirror X)",
                                     self.FONT_MAIN, self.SS['chk'])

        # ── Beam / Twiss section ──────────────────────────────────────────────

        def _build_beam_section(self, layout):
            _sec(layout, "Emittances", self.FONT_SEC)
            _help(layout,
                  "Geometric emittances used for beam size (σ = √(ε·β)) in the "
                  "Twiss Inspector and the 3D σ tube overlay.",
                  self.FONT_SMALL)

            r = _row(layout); _lbl(r, "εx (m·rad, geom.)", self.FONT_MAIN)
            self.w_emit_x = _ent(r, self.FONT_MONO, self.SS['entry'],
                                  width=110, placeholder="e.g. 1e-9")
            r = _row(layout); _lbl(r, "εy (m·rad, geom.)", self.FONT_MAIN)
            self.w_emit_y = _ent(r, self.FONT_MONO, self.SS['entry'],
                                  width=110, placeholder="e.g. 1e-9")
            r = _row(layout); _lbl(r, "σ_dp / p", self.FONT_MAIN)
            self.w_sigma_dp = _ent(r, self.FONT_MONO, self.SS['entry'],
                                    width=110, placeholder="e.g. 1e-3")

            _sec(layout, "Twiss Inspector — Plot Selection", self.FONT_SEC)
            _help(layout,
                  "Choose which quantities appear as panels in the popup inspector. "
                  "Beta and beam size require optics data from the backend. "
                  "Orbit requires .cen (ELEGANT) or equivalent.",
                  self.FONT_SMALL)

            self._inspector_chks = {}
            _plots = [
                ('beta',       'β functions (βx, βy)',         True),
                ('sigma',      'Beam size σx, σy  (needs ε)',  True),
                ('dispersion', 'Dispersion ηx, ηy',            False),
                ('orbit',      'Orbit x, y',                   False),
                ('phase',      'Phase advance μx, μy',         False),
            ]
            for key, label, default in _plots:
                r = _row(layout)
                cb = _chk(r, label, self.FONT_MAIN, self.SS['chk'])
                cb.setChecked(default)
                self._inspector_chks[key] = cb

            # Phase convention toggle on same row as phase checkbox
            r = _row(layout)
            lbl = QLabel("Phase units:"); lbl.setFont(self.FONT_SMALL)
            lbl.setStyleSheet(f"color:{FG_DIM};background:transparent;padding-left:12px;")
            r.addWidget(lbl)
            self.w_phase_norm = _dd(r, ["Cumulative (rad)", "Normalized (0→1 per 2π)"],
                                    self.FONT_SMALL, self.SS['combo'], width=180)

            _sec(layout, "3D σ Tube Overlay", self.FONT_SEC)
            r = _row(layout)
            self.w_show_twiss = _chk(r, "Show σ tube in 3D view",
                                      self.FONT_MAIN, self.SS['chk'])
            self.w_show_twiss.setChecked(False)

            r = _row(layout); _lbl(r, "Envelope scale", self.FONT_MAIN)
            self.w_twiss_scale = _ent(r, self.FONT_MONO, self.SS['entry'], width=70)
            self.w_twiss_scale.setText("1.0")
            _hint(r, "1=1σ, 3=3σ", self.FONT_SMALL)

            r = _row(layout); _lbl(r, "Tube opacity", self.FONT_MAIN)
            self.w_twiss_opacity = _ent(r, self.FONT_MONO, self.SS['entry'], width=70)
            self.w_twiss_opacity.setText("0.35")

            r = _row(layout); _lbl(r, "Tube segments", self.FONT_MAIN)
            self.w_twiss_nphi = _ent(r, self.FONT_MONO, self.SS['entry'], width=70)
            self.w_twiss_nphi.setText("16")
            _hint(r, "azimuthal res.", self.FONT_SMALL)

            r = _row(layout); _lbl(r, "σ_x color", self.FONT_MAIN)
            self.w_twiss_cx = _ent(r, self.FONT_MONO, self.SS['entry'], width=90)
            self.w_twiss_cx.setText("#74c0fc")
            _lbl(r, "σ_y color", self.FONT_MAIN, width=60)
            self.w_twiss_cy = _ent(r, self.FONT_MONO, self.SS['entry'], width=90)
            self.w_twiss_cy.setText("#69db7c")

            _sec(layout, "Magnet Size", self.FONT_SEC)
            _help(layout,
                  "Load an aperture definition file to overlay magnet apertures "
                  "in the 3D view. Format: name  shape  outer_x  outer_y",
                  self.FONT_SMALL)
            r = _row(layout); _lbl(r, "Magnet size file", self.FONT_MAIN)
            self.w_aperture_file = _ent(r, self.FONT_MONO, self.SS['entry'],
                                        width=200, placeholder="path/to/magnet_sizes.dat")
            _btn(r, "Browse", self._browse_aperture, self.FONT_MAIN, width=70)

        # ── Overlays section ──────────────────────────────────────────────────

        def _build_overlays_section(self, layout):
            _sec(layout, "Element Annotations", self.FONT_SEC)
            r = _row(layout); _lbl(r, "Pattern", self.FONT_MAIN)
            self.w_annot = _ent(r, self.FONT_MONO, self.SS['entry'],
                                 width=240, placeholder="e.g. IPM*, BPM*, IP*")
            r = _row(layout); _lbl(r, "Font size", self.FONT_MAIN)
            self.w_annot_size = _ent(r, self.FONT_MONO, self.SS['entry'], width=60)
            self.w_annot_size.setText("10")
            _help(layout,
                  "Comma-separated wildcard patterns. Adds 3D text labels at "
                  "matching elements.", self.FONT_SMALL)

            _sec(layout, "Tunnel Wall", self.FONT_SEC)
            r = _row(layout); _lbl(r, "Wall coord file", self.FONT_MAIN)
            self.w_tunnel_file = _ent(r, self.FONT_MONO, self.SS['entry'],
                                       width=200, placeholder="path/to/tunnel.dat")
            _btn(r, "Browse", self._browse_tunnel, self.FONT_MAIN, width=70)
            r = _row(layout)
            self.w_show_tunnel = _chk(r, "Draw tunnel wall",
                                       self.FONT_MAIN, self.SS['chk'])
            _help(layout,
                  "Format: x_in y_in z_in x_out y_out z_out per line.",
                  self.FONT_SMALL)

            _sec(layout, "Ground Plane", self.FONT_SEC)
            r = _row(layout)
            self.w_show_ground = _chk(r, "Draw ground plane",
                                       self.FONT_MAIN, self.SS['chk'])
            r = _row(layout); _lbl(r, "Ground Y position", self.FONT_MAIN)
            self.w_ground_y = _ent(r, self.FONT_MONO, self.SS['entry'], width=80)
            self.w_ground_y.setText("0.0")
            r = _row(layout)
            self.w_ground_grid = _chk(r, "Show grid on ground",
                                       self.FONT_MAIN, self.SS['chk'])
            self.w_ground_grid.setChecked(True)
            _help(layout,
                  "Useful for orientation. Place at the floor of your tunnel.",
                  self.FONT_SMALL)

        # ── Reactive UI ───────────────────────────────────────────────────────

        def _on_input_change(self, path):
            self._autodetect_code(path)
            if path.endswith('.init'):
                self._update_universe_selector(path)
            else:
                self._clear_universe_selector()

        def _autodetect_code(self, path):
            ext = Path(path).suffix.lower()
            if ext == '.init':
                self.w_code.setCurrentText('tao')
            elif ext == '.ele':
                self.w_code.setCurrentText('elegant')
            elif ext == '.json':
                self.w_code.setCurrentText('xsuite')
            elif ext == '.tfs':
                self.w_code.setCurrentText('madx')
            self._update_xsuite_rows()
            self._update_madx_rows()

        def _update_xsuite_rows(self):
            if self.w_code.currentText() == 'xsuite':
                self._xsuite_widget.show()
            else:
                self._xsuite_widget.hide()

        def _update_madx_rows(self):
            if self.w_code.currentText() == 'madx':
                self._madx_widget.show()
            else:
                self._madx_widget.hide()

        def _clear_universe_selector(self):
            while self._uni_checks_v.count():
                item = self._uni_checks_v.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._uni_checks = {}; self._uni_label_edits = {}
            self._uni_n = 1
            placeholder = QLabel("(Single-universe lattice — no selection needed)")
            placeholder.setFont(self.FONT_SMALL)
            placeholder.setStyleSheet(f"color: {FG_DIM}; padding: 4px 12px;")
            self._uni_checks_v.addWidget(placeholder)

        def _update_universe_selector(self, path):
            while self._uni_checks_v.count():
                item = self._uni_checks_v.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self._uni_checks = {}; self._uni_label_edits = {}
            try:
                n, labels = _parse_tao_init(path)
            except Exception:
                self._clear_universe_selector(); return
            self._uni_n = n
            if n <= 1:
                self._clear_universe_selector(); return
            for i in range(1, n + 1):
                lbl = labels.get(i, f'u{i}')
                cell = QWidget(); cell.setStyleSheet("background: transparent;")
                cell_h = QHBoxLayout(cell)
                cell_h.setContentsMargins(0, 0, 0, 0); cell_h.setSpacing(4)
                cb = QCheckBox(f"u{i}"); cb.setChecked(True)
                cb.setFont(self.FONT_MAIN); cb.setStyleSheet(self.SS['chk'])
                cell_h.addWidget(cb)
                le = QLineEdit(lbl); le.setFixedWidth(140)
                le.setFont(self.FONT_MAIN); le.setStyleSheet(self.SS['entry'])
                cell_h.addWidget(le)
                self._uni_checks[i] = cb; self._uni_label_edits[i] = le
                self._uni_checks_v.addWidget(cell)

        def _get_selected_universes(self):
            if not self._uni_checks or self._uni_n <= 1:
                return None
            sel = [i for i, cb in self._uni_checks.items() if cb.isChecked()]
            return sel if sel else None

        # ── File dialogs ──────────────────────────────────────────────────────

        def _browse_input(self):
            f, _ = QFileDialog.getOpenFileName(
                self, "Select input file", "",
                "All supported (*.init *.ele *.json *.tfs);;"
                "Tao init (*.init);;ELEGANT (*.ele);;"
                "xsuite JSON (*.json);;MAD-X TFS (*.tfs);;All files (*.*)")
            if f:
                self.w_input.setText(f)

        def _browse_madx_survey(self):
            f, _ = QFileDialog.getOpenFileName(
                self, "Select MAD-X survey file", "",
                "TFS files (*.tfs);;All files (*.*)")
            if f:
                self.w_madx_survey.setText(f)

        def _browse_tunnel(self):
            f, _ = QFileDialog.getOpenFileName(
                self, "Select tunnel wall file", "",
                "Data files (*.dat *.txt *.csv);;All files (*.*)")
            if f:
                self.w_tunnel_file.setText(f)

        def _browse_aperture(self):
            f, _ = QFileDialog.getOpenFileName(
                self, "Select aperture definition file", "",
                "Data files (*.dat *.txt *.csv);;All files (*.*)")
            if f:
                self.w_aperture_file.setText(f)

        def _browse_output(self):
            f, _ = QFileDialog.getSaveFileName(
                self, "Save output HTML", "optics3d.html",
                "HTML files (*.html);;All files (*.*)")
            if f:
                self.w_output.setText(f)

        # ── Collect kwargs ────────────────────────────────────────────────────

        def _collect_kwargs(self):
            inp = self.w_input.text().strip()
            if not inp:
                raise ValueError("Please select an input file.")

            def _f(widget, default=None):
                t = widget.text().strip()
                if not t:
                    return default
                try:
                    return float(t)
                except ValueError:
                    raise ValueError(f"Invalid number: '{t}'")

            def _i(widget, default=None):
                t = widget.text().strip()
                if not t:
                    return default
                try:
                    return int(t)
                except ValueError:
                    raise ValueError(f"Invalid integer: '{t}'")

            aspect_map = {
                "data (real proportions)": "data",
                "manual (X/Y/Z scale)": "manual",
                "cube (equal axes)": "cube",
            }
            aspect_v = aspect_map.get(self.w_aspect.currentText(), "data")

            visible = {n for n, cb in self._type_chk_widgets.items() if cb.isChecked()}
            opacity = {}
            for n, e in self._type_op_widgets.items():
                t = e.text().strip()
                if not t:
                    continue
                try:
                    opacity[n] = float(t)
                except ValueError:
                    pass

            return dict(
                input_file=inp,
                code=self.w_code.currentText(),
                output_file=self.w_output.text().strip() or "optics3d.html",
                title=self.w_title.text().strip() or None,
                flip_bend=self.w_flip_bend.isChecked(),
                element_half_width=_f(self.w_half_w, 0.2),
                element_half_height=_f(self.w_half_h, 0.2),
                show_beampipe=self.w_show_pipe.isChecked(),
                beampipe_color=self.w_pipe_color.text().strip() or "#888888",
                beampipe_width=_i(self.w_pipe_width, 2),
                show_markers=self.w_show_markers.isChecked(),
                show_outlines=self.w_show_outlines.isChecked(),
                bend_segments=_i(self.w_bend_seg, 12),
                dark_mode=self.w_dark.isChecked(),
                show=False,
                universes=self._get_selected_universes(),
                xsuite_line=self.w_xsuite_line.text().strip() or None,
                madx_survey=self.w_madx_survey.text().strip() or None,
                aspect=aspect_v,
                scale_x=_f(self.w_scale_x, 1.0),
                scale_y=_f(self.w_scale_y, 1.0),
                scale_z=_f(self.w_scale_z, 1.0),
                srange=self.w_range.text().strip() or None,
                visible_types=visible,
                type_opacity=opacity,
                annotation_pattern=self.w_annot.text().strip() or None,
                annotation_font_size=_i(self.w_annot_size, 10),
                tunnel_wall_file=self.w_tunnel_file.text().strip() or None,
                show_tunnel=self.w_show_tunnel.isChecked(),
                show_ground=self.w_show_ground.isChecked(),
                ground_y=_f(self.w_ground_y, 0.0),
                ground_grid=self.w_ground_grid.isChecked(),
                show_axes_gizmo=self.w_show_gizmo.isChecked(),
                z_up=self.w_z_up.isChecked(),
                camera_preset=self.w_camera.currentText(),
                camera_eye=_parse_camera_eye(self.w_camera_eye.text()),
                focus_element=self.w_focus_elem.text().strip() or None,
                focus_radius=_f(self.w_focus_radius, None),
                add_control_panel=self.w_control_panel.isChecked(),
                show_twiss=self.w_show_twiss.isChecked(),
                aperture_file=self.w_aperture_file.text().strip() or None,
                emit_x=_f(self.w_emit_x, None),
                emit_y=_f(self.w_emit_y, None),
                sigma_dp=_f(self.w_sigma_dp, None),
                twiss_scale=_f(self.w_twiss_scale, 1.0),
                twiss_tube_opacity=_f(self.w_twiss_opacity, 0.35),
                twiss_n_phi=_i(self.w_twiss_nphi, 16),
                twiss_x_color=self.w_twiss_cx.text().strip() or '#74c0fc',
                twiss_y_color=self.w_twiss_cy.text().strip() or '#69db7c',
                inspector_plots=[k for k, cb in self._inspector_chks.items()
                                 if cb.isChecked()],
                phase_normalized=(self.w_phase_norm.currentIndex() == 1),
            )

        # ── Run / inspect ─────────────────────────────────────────────────────

        def _run(self):
            try:
                kwargs = self._collect_kwargs()
            except ValueError as e:
                QMessageBox.critical(self, "Configuration Error", str(e))
                return

            self.run_btn.setEnabled(False); self.dryrun_btn.setEnabled(False)
            self.open_btn.setEnabled(False)
            self.open_btn.setStyleSheet("")
            self._set_status("Rendering…")
            self._log("\n" + "─" * 60 + "\n", "dim")
            self._log(f"▶ code={kwargs['code']}  aspect={kwargs['aspect']}  "
                      f"scale=({kwargs['scale_x']},{kwargs['scale_y']},"
                      f"{kwargs['scale_z']})\n", "info")
            self._log("─" * 60 + "\n", "dim")

            def _worker():
                try:
                    kwargs['log_fn'] = lambda m: self._sig_log.emit(m, _clf(m))
                    plot_optics_3d(**kwargs)
                    out = str(Path(kwargs['output_file']).resolve())
                    self._last_output = out
                    self._sig_log.emit(f"\n✓ Done — {out}\n", "ok")
                    self._sig_done.emit(kwargs['input_file'])
                except Exception:
                    import traceback
                    tb = traceback.format_exc()
                    self._sig_log.emit(f"\n✗ Error:\n{tb}\n", "error")
                finally:
                    self._sig_finally.emit()

            threading.Thread(target=_worker, daemon=True).start()

        def _dry_run(self):
            try:
                kwargs = self._collect_kwargs()
            except ValueError as e:
                QMessageBox.critical(self, "Configuration Error", str(e))
                return

            self.run_btn.setEnabled(False); self.dryrun_btn.setEnabled(False)
            self._set_status("Inspecting lattice…")
            self._log("\n🔍 Inspecting lattice…\n", "info")

            def _worker():
                try:
                    code = kwargs['code']; inp = kwargs['input_file']
                    log = lambda m: self._sig_log.emit(m, "info")
                    if code == 'tao':
                        data = load_tao(inp, log_fn=log)
                    elif code == 'elegant':
                        data = load_elegant(inp, log_fn=log)
                    elif code == 'xsuite':
                        data = load_xsuite(inp, log_fn=log,
                                            line_name=kwargs.get('xsuite_line'))
                    elif code == 'madx':
                        data = load_madx(inp,
                                          survey_file=kwargs.get('madx_survey'),
                                          log_fn=log)
                    else:
                        raise ValueError(f"Unknown code: {code}")
                    elems = data.get('elements', [])
                    stats = compute_lattice_stats(elems)
                    msg = (f"\n✓ {stats['n_elements']} elements — "
                           f"total length = {stats['total_length']:.3f} m\n")
                    msg += "  " + ", ".join(
                        f"{c}: {n}" for c, n in stats['counts'].items()) + "\n"
                    self._sig_log.emit(msg, "ok")
                    s_str = ", ".join(f"{c}:{n}"
                                      for c, n in stats['counts'].items())
                    self._sig_log.emit(f"[stats] {s_str}\n", "dim")
                except Exception:
                    import traceback
                    tb = traceback.format_exc()
                    self._sig_log.emit(f"\n✗ Error:\n{tb}\n", "error")
                finally:
                    self._sig_finally.emit()

            threading.Thread(target=_worker, daemon=True).start()

        def _open_plot(self):
            import webbrowser
            if self._last_output and Path(self._last_output).exists():
                webbrowser.open(f"file://{self._last_output}")
            else:
                QMessageBox.warning(self, "Open Plot",
                                    "No output yet. Render first.")

        def _on_run_done(self, input_file):
            self.open_btn.setEnabled(True)
            self.open_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {SUCCESS}; border: 1px solid {SUCCESS};
                    border-radius: 8px; color: {CRUST}; font-weight: bold;
                }}
                QPushButton:hover {{ background: {SUCCESS}; color: {CRUST}; opacity: 0.9; }}
            """)
            self._save_recent(input_file)
            self._set_status("Done ✓")

        def _on_run_finally(self):
            self.run_btn.setEnabled(True)
            self.dryrun_btn.setEnabled(True)

        def _copy_path(self):
            if self._last_output:
                QApplication.clipboard().setText(self._last_output)
                self._set_status("Path copied ✓")
            else:
                QMessageBox.warning(self, "Copy Path", "No output yet.")

        # ── Log ───────────────────────────────────────────────────────────────

        _LOG_COLORS = {"ok": SUCCESS, "warn": WARN, "error": ERROR,
                       "dim": FG_DIM, "info": FG}

        def _log(self, text, tag="info"):
            color = self._LOG_COLORS.get(tag, FG)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            fmt.setFont(self.FONT_MONO)
            cursor = self.log.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.setCharFormat(fmt)
            cursor.insertText(text)
            self.log.setTextCursor(cursor)
            self.log.ensureCursorVisible()

        def _clear_log(self):
            self.log.clear()
            self._log("Log cleared.\n", "dim")

        # ── Recent files ──────────────────────────────────────────────────────

        def _load_recent(self):
            try:
                import json
                data = json.loads(self._RECENT_FILE.read_text())
                return [p for p in data if Path(p).exists()]
            except Exception:
                return []

        def _save_recent(self, path):
            import json
            recent = [p for p in self._load_recent() if p != path]
            recent.insert(0, path)
            try:
                self._RECENT_FILE.write_text(json.dumps(recent[:self._MAX_RECENT]))
            except Exception:
                pass
            self._refresh_recent_menu()

        def _refresh_recent_menu(self):
            if not hasattr(self, '_recent_menu'):
                return
            self._recent_menu.clear()
            recent = self._load_recent()
            if not recent:
                a = QAction("(no recent files)", self); a.setEnabled(False)
                self._recent_menu.addAction(a); return
            for p in recent:
                label = Path(p).name + "  —  " + str(Path(p).parent)
                act = QAction(label, self)
                act.triggered.connect(lambda _=False, f=p: self.w_input.setText(f))
                self._recent_menu.addAction(act)

        # ── Presets ───────────────────────────────────────────────────────────

        def _load_presets(self):
            try:
                import json
                return json.loads(self._PRESET_FILE.read_text())
            except Exception:
                return {}

        def _save_presets(self, presets):
            import json
            try:
                self._PRESET_FILE.write_text(json.dumps(presets, indent=2))
            except Exception as e:
                QMessageBox.critical(self, "Preset Error", str(e))

        def _collect_preset(self):
            return {
                'code':         self.w_code.currentText(),
                'output':       self.w_output.text(),
                'title':        self.w_title.text(),
                'range':        self.w_range.text(),
                'aspect':       self.w_aspect.currentText(),
                'scale_x':      self.w_scale_x.text(),
                'scale_y':      self.w_scale_y.text(),
                'scale_z':      self.w_scale_z.text(),
                'camera':       self.w_camera.currentText(),
                'camera_eye':   self.w_camera_eye.text(),
                'focus_elem':   self.w_focus_elem.text(),
                'focus_radius': self.w_focus_radius.text(),
                'z_up':         self.w_z_up.isChecked(),
                'dark':         self.w_dark.isChecked(),
                'show_gizmo':   self.w_show_gizmo.isChecked(),
                'control_panel': self.w_control_panel.isChecked(),
                'show_pipe':    self.w_show_pipe.isChecked(),
                'pipe_color':   self.w_pipe_color.text(),
                'pipe_width':   self.w_pipe_width.text(),
                'half_w':       self.w_half_w.text(),
                'half_h':       self.w_half_h.text(),
                'bend_seg':     self.w_bend_seg.text(),
                'show_markers': self.w_show_markers.isChecked(),
                'flip_bend':    self.w_flip_bend.isChecked(),
                'annot':        self.w_annot.text(),
                'annot_size':   self.w_annot_size.text(),
                'tunnel_file':  self.w_tunnel_file.text(),
                'show_tunnel':  self.w_show_tunnel.isChecked(),
                'show_ground':  self.w_show_ground.isChecked(),
                'ground_y':     self.w_ground_y.text(),
                'ground_grid':  self.w_ground_grid.isChecked(),
                'type_visible': {n: cb.isChecked()
                                  for n, cb in self._type_chk_widgets.items()},
                'type_opacity': {n: e.text()
                                  for n, e in self._type_op_widgets.items()},
            }

        def _apply_preset(self, data):
            def _st(w, k):
                if k in data and hasattr(w, 'setText'):
                    w.setText(str(data[k]))

            def _sc(w, k):
                if k in data and hasattr(w, 'setChecked'):
                    w.setChecked(bool(data[k]))

            def _sct(w, k):
                if k in data and hasattr(w, 'setCurrentText'):
                    w.setCurrentText(str(data[k]))

            _sct(self.w_code, 'code'); _st(self.w_output, 'output')
            _st(self.w_title, 'title'); _st(self.w_range, 'range')
            _sct(self.w_aspect, 'aspect')
            _st(self.w_scale_x, 'scale_x'); _st(self.w_scale_y, 'scale_y')
            _st(self.w_scale_z, 'scale_z')
            _sct(self.w_camera, 'camera')
            _st(self.w_camera_eye, 'camera_eye')
            _st(self.w_focus_elem, 'focus_elem')
            _st(self.w_focus_radius, 'focus_radius')
            _sc(self.w_z_up, 'z_up'); _sc(self.w_dark, 'dark')
            _sc(self.w_show_gizmo, 'show_gizmo')
            _sc(self.w_control_panel, 'control_panel')
            _sc(self.w_show_pipe, 'show_pipe')
            _st(self.w_pipe_color, 'pipe_color')
            _st(self.w_pipe_width, 'pipe_width')
            _st(self.w_half_w, 'half_w'); _st(self.w_half_h, 'half_h')
            _st(self.w_bend_seg, 'bend_seg')
            _sc(self.w_show_markers, 'show_markers')
            _sc(self.w_flip_bend, 'flip_bend')
            _st(self.w_annot, 'annot'); _st(self.w_annot_size, 'annot_size')
            _st(self.w_tunnel_file, 'tunnel_file')
            _sc(self.w_show_tunnel, 'show_tunnel')
            _sc(self.w_show_ground, 'show_ground')
            _st(self.w_ground_y, 'ground_y')
            _sc(self.w_ground_grid, 'ground_grid')
            for n, v in (data.get('type_visible') or {}).items():
                if n in self._type_chk_widgets:
                    self._type_chk_widgets[n].setChecked(bool(v))
            for n, v in (data.get('type_opacity') or {}).items():
                if n in self._type_op_widgets:
                    self._type_op_widgets[n].setText(str(v))

        def _preset_save_dialog(self):
            name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
            if not ok or not name:
                return
            presets = self._load_presets()
            presets[name] = self._collect_preset()
            self._save_presets(presets); self._refresh_preset_menu()
            self._log(f"[preset] Saved '{name}'\n", "ok")

        def _preset_delete_dialog(self):
            presets = self._load_presets()
            if not presets:
                QMessageBox.information(self, "Delete Preset", "No saved presets.")
                return
            name, ok = QInputDialog.getText(
                self, "Delete Preset",
                "Preset to delete:\n" + ", ".join(presets.keys()))
            if ok and name and name in presets:
                del presets[name]
                self._save_presets(presets); self._refresh_preset_menu()
                self._log(f"[preset] Deleted '{name}'\n", "warn")

        def _refresh_preset_menu(self):
            if not hasattr(self, '_preset_menu'):
                return
            self._preset_menu.clear()
            presets = self._load_presets()
            if not presets:
                a = QAction("(no saved presets)", self); a.setEnabled(False)
                self._preset_menu.addAction(a); return
            for name in presets:
                act = QAction(name, self)
                act.triggered.connect(
                    lambda _=False, n=name:
                    self._apply_preset(self._load_presets().get(n, {})))
                self._preset_menu.addAction(act)


# ════════════════════════════════════════════════════════════════════════════
#  Entry point
# ════════════════════════════════════════════════════════════════════════════
