"""Common tools used by scripts.
"""

import argparse
from pathlib import Path


def common_parse_args(doc=__doc__):
    parser = argparse.ArgumentParser(description=doc)
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument(
        "--endpoint", default="https://www.hackinscience.org/api/exercises/"
    )
    args, remaining = parser.parse_known_args()
    if not args.username or not args.password:
        args.username, args.password = (
            (Path.home() / ".hkis")
            .read_text(encoding="UTF-8")
            .rstrip()
            .split(":", maxsplit=1)
        )
    return args, remaining
