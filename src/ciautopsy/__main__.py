"""Package entrypoint: python -m ciautopsy."""

import sys

from ciautopsy.cli import main

if __name__ == "__main__":
    sys.exit(main())
