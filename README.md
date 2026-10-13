# pyfig

> **Warning:** This project was fully written by an AI agent, has not been fully human-tested, and should be run at your own risk.


`pyfig` saves a Matplotlib `Figure` as a Python pickle with the `.pyfig`
extension, then lets you reopen the editable figure later.

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

**Only open `.pyfig` files from sources you trust.** They are pickle files, and
loading a pickle can execute arbitrary code. Figures containing custom artists
may also need their original Python modules installed. Pickles work best with
the same Matplotlib version used to save them.

Run the tests without a display server:

```sh
MPLBACKEND=Agg python3 -m unittest discover -s tests -v
```
