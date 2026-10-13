"""Save and load Matplotlib figures as ``.pyfig`` pickle files."""

import pickle
from pathlib import Path

from matplotlib.figure import Figure

__all__ = ["save_figure", "load_figure"]


def save_figure(figure: Figure, path) -> Path:
    """Pickle *figure* to *path*, appending ``.pyfig`` when needed.

    Returns the path actually written. Existing files are overwritten.
    """
    if not isinstance(figure, Figure):
        raise TypeError("figure must be a matplotlib.figure.Figure")

    destination = Path(path)
    if destination.suffix != ".pyfig":
        destination = destination.with_name(destination.name + ".pyfig")

    with destination.open("wb") as file:
        pickle.dump(figure, file, protocol=pickle.HIGHEST_PROTOCOL)
    return destination


def load_figure(path) -> Figure:
    """Load a figure from a trusted ``.pyfig`` pickle file.

    Unpickling can execute arbitrary code. Only load files you trust.
    """
    with Path(path).open("rb") as file:
        figure = pickle.load(file)
    if not isinstance(figure, Figure):
        raise TypeError("file does not contain a matplotlib.figure.Figure")
    return figure
