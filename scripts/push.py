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
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.username:
        args.username = input("Username: ")
    if not args.password:
        args.password = getpass()
    for exercise in Path("exercises").glob("*/"):
        with open(exercise / "meta") as f:
            meta = json.load(f)
        if args.only:
            if args.only not in meta["slug"]:
                continue
        for file in (
            "check.py",
            "solution.py",
            "wording.md",
            "wording_fr.md",
            "wording_en.md",
            "initial_solution.py",
        ):
            meta[file.split(".")[0]] = (exercise / (file)).read_text()
        print("Uploading ", meta["title"])
        response = requests.put(
            meta["url"], json=meta, auth=(args.username, args.password)
        )
        response.raise_for_status()


if __name__ == "__main__":
    main()
