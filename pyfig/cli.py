"""Command-line opener for saved Matplotlib figures."""

import argparse

import matplotlib._pylab_helpers as pylab_helpers
import matplotlib.pyplot as plt

from . import load_figure


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Open a trusted .pyfig figure")
    parser.add_argument("file", help="path to a .pyfig file")
    args = parser.parse_args(argv)

    figure = load_figure(args.file)
    if figure.canvas.manager is None:
        # Figures created without pyplot need a GUI manager before show().
        numbers = plt.get_fignums()
        number = max(numbers) + 1 if numbers else 1
        manager = plt._get_backend_mod().new_figure_manager_given_figure(number, figure)
        pylab_helpers.Gcf._set_new_active_manager(manager)
    plt.show()
    return 0
