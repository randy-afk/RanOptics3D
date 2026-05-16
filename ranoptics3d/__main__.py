"""
Allows running the package directly:

    python -m ranoptics3d
    python -m ranoptics3d /path/to/tao.init --code tao
    python -m ranoptics3d --gui
"""
from .cli import main

if __name__ == '__main__':
    main()
