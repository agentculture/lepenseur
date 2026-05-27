"""Allow running model-gear as ``python -m model_gear``."""

import sys

from model_gear.cli import main

if __name__ == "__main__":
    sys.exit(main())
