"""tao_example.py — render a tao lattice in 3D."""
import argparse
from ranoptics3d import plot_optics_3d

def main():
    p = argparse.ArgumentParser()
    p.add_argument('input_file')
    p.add_argument('--output', default='lattice3d.html')
    p.add_argument('--light', action='store_true')
    a = p.parse_args()
    plot_optics_3d(a.input_file, code='tao', output_file=a.output,
                   dark_mode=not a.light, show=True,
                   log_fn=lambda m: print(m, end=''))

if __name__ == '__main__': main()
