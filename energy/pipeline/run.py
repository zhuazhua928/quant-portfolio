"""End-to-end CLI: pull + compute + export.

Usage:
    python -m energy.pipeline.run
"""

from __future__ import annotations

import logging
import sys

from ..export.export_dashboard import export_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> int:
    paths = export_all()
    print()
    for k, p in paths.items():
        print(f"  {k:8s} -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
