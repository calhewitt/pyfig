# Repository notes

- Use Python 3.9 or newer; the system `python` command may be Python 2.
- New `.pyfig` files are compact ZIP archives containing a figure pickle, shared NumPy arrays, and a versioned manifest. `load_figure` also reads legacy direct Figure pickles.
- Reject custom Artist subclasses in the compact format rather than silently changing their output.
- Saving may clear recomputable `Line2D` caches on the source figure; its public data and rendered output must remain unchanged.
- Run `MPLBACKEND=Agg python3 -m unittest discover -s tests -v` after changes.
- Never unpickle an untrusted file in tests or examples.
