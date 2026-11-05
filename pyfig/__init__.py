"""Save and load Matplotlib figures as ``.pyfig`` files."""

import pickle
from pathlib import Path

from matplotlib.figure import Figure

from .compact import UnsupportedFigureError, load_compact_figure, save_compact_figure

__all__ = ["save_figure", "load_figure", "UnsupportedFigureError"]


def save_figure(figure: Figure, path) -> Path:
    """Save *figure* compactly, appending ``.pyfig`` when needed.

    Returns the path actually written. Existing files are overwritten.
    """
    return save_compact_figure(figure, path)


def load_figure(path) -> Figure:
    """Load a figure from a trusted ``.pyfig`` file, including legacy pickles.

    Unpickling can execute arbitrary code. Only load files you trust.
    """
    source = Path(path)
    with source.open("rb") as file:
        signature = file.read(4)
    if signature == b"PK\x03\x04":
        return load_compact_figure(source)
    with source.open("rb") as file:
        figure = pickle.load(file)
    if not isinstance(figure, Figure):
        raise TypeError("file does not contain a matplotlib.figure.Figure")
    return figure
