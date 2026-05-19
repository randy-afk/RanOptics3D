"""
ranoptics3d
===========
3D Accelerator Lattice Layout Viewer.

Renders accelerator beamlines in 3D using survey (floor) coordinates
from Tao/Bmad, ELEGANT, xsuite, or MAD-X. Produces a self-contained
interactive HTML file with a live control panel.

Quick start
-----------
    from ranoptics3d import plot_optics_3d
    plot_optics_3d('tao.init', output_file='lattice3d.html', show=True)

    # Or from the command line:
    ranoptics3d /path/to/tao.init
    ranoptics3d /path/to/run.ele --code elegant
    ranoptics3d --gui
"""

__version__ = '1.1.0'
__author__  = 'Randika Gamage (randika@jlab.org)'
__support__ = r'¯\_(ツ)_/¯  (good luck, I believe in you)'
__license__ = 'MIT'

from ._plot import plot_optics_3d, compute_lattice_stats
from ._elements import element_color, element_legend, make_hover
from ._backends import load_tao, load_elegant, load_xsuite, load_madx

__all__ = [
    'plot_optics_3d',
    'compute_lattice_stats',
    'element_color',
    'element_legend',
    'make_hover',
    'load_tao',
    'load_elegant',
    'load_xsuite',
    'load_madx',
]
