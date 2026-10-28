"""Start the Network Health Checker prototype.

Usage:
    python src/main.py data/sample_targets.txt
    python src/main.py --gui
"""

import sys

from network_health_checker.cli import main

if __name__ == "__main__":
    sys.exit(main())
