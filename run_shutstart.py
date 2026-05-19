"""PyInstaller entry shim — runs the package as `python -m shutstart` would.

`shutstart/__main__.py` uses relative imports (`from . import ...`), which
require the script to live inside a package. PyInstaller's Analysis target,
however, is executed as a top-level script with no parent package, so the
relative import fails at startup. This shim is the top-level script instead;
it imports the package proper and dispatches to `main()`.
"""
from __future__ import annotations

import sys

from shutstart.__main__ import main


if __name__ == "__main__":
    sys.exit(main())
