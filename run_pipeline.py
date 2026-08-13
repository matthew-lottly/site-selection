#!/usr/bin/env python
"""Entry point for the Houston Family Dollar site-selection pipeline.

Usage:
    python run_pipeline.py                # run every stage, in order
    python run_pipeline.py --only 01 02    # run only the given stage ids
    python run_pipeline.py --list          # list every stage and exit

Each stage also remains directly runnable on its own, e.g.:
    python -m pipeline.stages.s01_fetch_tracts
"""
from __future__ import annotations

import argparse

from pipeline.core import Pipeline
from pipeline.stages import ALL_STAGES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="*", metavar="ID", help="run only these stage ids, e.g. --only 01 02")
    parser.add_argument("--list", action="store_true", help="list every stage and exit")
    args = parser.parse_args()

    pipeline = Pipeline(ALL_STAGES)

    if args.list:
        pipeline.list_stages()
        return

    only = set(args.only) if args.only else None
    pipeline.run_all(only=only)


if __name__ == "__main__":
    main()
