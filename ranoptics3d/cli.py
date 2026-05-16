"""
ranoptics3d.cli
===============
Command-line entry point.
"""
from __future__ import annotations
import sys


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog='ranoptics3d',
        description='3D Accelerator Lattice Layout Viewer',
    )
    parser.add_argument('lattice', nargs='?', default=None)
    parser.add_argument('--code', default='auto',
                        choices=['auto','tao','elegant','xsuite','madx'])
    parser.add_argument('--survey', default=None)
    parser.add_argument('--output', default='lattice3d.html')
    parser.add_argument('--dark', dest='dark', action='store_true', default=True)
    parser.add_argument('--no-dark', dest='dark', action='store_false')
    parser.add_argument('--show-markers', action='store_true', default=False)
    parser.add_argument('--half-width',   type=float, default=0.2, metavar='W')
    parser.add_argument('--half-height',  type=float, default=0.2, metavar='H')
    parser.add_argument('--bend-segments',type=int,   default=12,  metavar='N')
    parser.add_argument('--s-start',      type=float, default=None)
    parser.add_argument('--s-end',        type=float, default=None)
    parser.add_argument('--gui', action='store_true')
    args = parser.parse_args()

    if args.gui or args.lattice is None:
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QColor, QPalette
        except ImportError:
            print("PySide6 required for GUI → pip install PySide6", file=sys.stderr)
            sys.exit(1)
        from ._gui import RanOptics3DGUI, _HAVE_PYSIDE, BG, FG, PANEL, ACCENT, FG_DIM
        if not _HAVE_PYSIDE:
            print("PySide6 not available.", file=sys.stderr); sys.exit(1)
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        pal = QPalette()
        for role, col in [
            (QPalette.Window, BG), (QPalette.WindowText, FG),
            (QPalette.Base, PANEL), (QPalette.AlternateBase, BG),
            (QPalette.Text, FG), (QPalette.Button, PANEL),
            (QPalette.ButtonText, FG), (QPalette.Highlight, ACCENT),
            (QPalette.HighlightedText, FG), (QPalette.PlaceholderText, FG_DIM),
        ]:
            pal.setColor(role, QColor(col))
        app.setPalette(pal)
        win = RanOptics3DGUI(); win.show(); sys.exit(app.exec())
    else:
        from ._plot import plot_optics_3d
        srange = None
        if args.s_start is not None and args.s_end is not None:
            srange = f'{args.s_start}:{args.s_end}'
        plot_optics_3d(
            args.lattice, code=args.code, output_file=args.output,
            madx_survey=args.survey, dark_mode=args.dark,
            show_markers=args.show_markers,
            element_half_width=args.half_width,
            element_half_height=args.half_height,
            bend_segments=args.bend_segments, srange=srange,
            show=True, log_fn=lambda m: print(m, end=''),
        )


if __name__ == '__main__':
    main()
