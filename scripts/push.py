"""Push back exercises via hackinscience API.
"""
import argparse
from getpass import getpass
from pathlib import Path
import json

import requests


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--only")
    parser.add_argument(
        "--endpoint", default="https://www.hackinscience.org/api/exercises/"
    )
    args = parser.parse_args()
    if not args.username or not args.password:
        args.username, args.password = (
            (Path.home() / ".hkis")
            .read_text(encoding="UTF-8")
            .rstrip()
            .split(":", maxsplit=1)
        )
    return args


def main():
    args = parse_args()
    for exercise in Path(".").glob("*/*/meta"):
        meta = json.loads(exercise.read_text())
        if args.only:
            if args.only not in meta["slug"]:
                continue
        for file in (
            "pre_check.py",
            "check.py",
            "wording_fr.md",
            "wording_en.md",
            "initial_solution.py",
        ):
            meta[file.split(".")[0]] = (exercise.parent / file).read_text()
        print("Uploading ", meta["title"])
        response = requests.put(
            meta["url"], json=meta, auth=(args.username, args.password)
        )
        response.raise_for_status()


if __name__ == "__main__":
    main()
