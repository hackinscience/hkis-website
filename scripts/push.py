"""Push back exercises via hackinscience API.
"""
import argparse
from pathlib import Path
import json

import requests

from utils import common_parse_args


def parse_args():
    args, remaining = common_parse_args(__doc__)
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    return parser.parse_args(remaining, args)


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
