#!/usr/bin/env python3
"""
Convenience script — run from the pkg/ directory without installing:

    python run.py
    python run.py /path/to/tao.init
    python run.py /path/to/run.ele --code elegant
    python run.py --gui

Equivalent to: python -m ranoptics3d [args]
"""
from ranoptics3d.cli import main

if __name__ == '__main__':
    main()
