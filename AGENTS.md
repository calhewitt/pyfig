# Repository notes

- Use Python 3.9 or newer; the system `python` command may be Python 2.
- Keep the file format a direct pickle of a Matplotlib `Figure` with the `.pyfig` extension.
- Run `MPLBACKEND=Agg python3 -m unittest discover -s tests -v` after changes.
- Never unpickle an untrusted file in tests or examples.
