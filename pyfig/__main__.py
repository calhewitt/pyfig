"""Allow ``python -m pyfig figure.pyfig``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
