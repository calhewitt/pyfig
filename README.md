# pyfig

> **Warning:** This project was fully written by an AI agent, has not been fully human-tested, and should be run at your own risk.


`pyfig` saves an editable Matplotlib `Figure` in a compact `.pyfig` archive.
It rebuilds large line drawing caches when you reopen the figure and stores
repeated numeric arrays only once. Existing `.pyfig` files containing direct
Figure pickles still open.

Requires Python 3.9 or newer and Matplotlib. Install from this directory:

```sh
python3 -m pip install -e .
```

To install into the system Python's user site and add its script directory to
your default fish path, run `./install_user.sh`. This uses the locally installed
setuptools and does not download build tools. Matplotlib must already be
installed for that Python.

Save and load a figure in Python:

```python
import matplotlib.pyplot as plt
from pyfig import load_figure, save_figure

figure, axes = plt.subplots()
axes.plot([1, 2, 3], [4, 5, 6])
path = save_figure(figure, "example")  # Writes example.pyfig.

restored = load_figure(path)
restored.axes[0].set_title("Still editable")
```

The compact format supports standard Matplotlib artists, including lines,
images, and collections. A custom `Artist` subclass raises
`UnsupportedFigureError` when saved, so it cannot silently change appearance.
Compression and cache rebuilding make saving and opening take more work than a
plain pickle; size savings depend on the plotted data. The archive contains a
pickle for the figure's layout and style, so it remains tied to compatible
Matplotlib versions. Saving clears recomputable drawing caches on the source
figure; its next draw rebuilds them. The format stores the derived arrays
already present in the figure and does not rerun the analysis script. Custom
artists, including some third-party and 3D artists, are rejected by the compact
saver.

To open the saved figure in a Matplotlib window, run any of:

```sh
pyfig-open example.pyfig
open_pyfig example.pyfig
python3 -m pyfig example.pyfig
python3 open_pyfig.py example.pyfig
```

To make Nautilus open `.pyfig` files on double-click, run
`./setup_nautilus.sh`. It installs a user-level MIME definition, registers
`open_pyfig` as its default application, installs a filetype icon, and installs
the command if needed. Run it again after changing the icon.

Opening a window requires a working graphical Matplotlib backend. The opener
uses `plt.show()`, so it waits for the window to close in normal noninteractive
use. `save_figure` returns the path it wrote and overwrites an existing file.

**Only open `.pyfig` files from sources you trust.** Both compact archives and
legacy files contain pickle data, and loading a pickle can execute arbitrary
code. Figures work best with the same Matplotlib version used to save them.

Run the tests without a display server:

```sh
MPLBACKEND=Agg python3 -m unittest discover -s tests -v
```
