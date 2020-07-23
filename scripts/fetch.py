"""Fetch exercises from hackinscience API.
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
    next_exercise_page = args.endpoint
    while next_exercise_page:
        exercises = requests.get(
            next_exercise_page, auth=(args.username, args.password)
        ).json()
        if "results" not in exercises:
            print(exercises)
            exit(1)
        translatables = []
        for exercise in exercises["results"]:
            path = Path("exercises") / exercise["slug"]
            path.mkdir(exist_ok=True, parents=True)
            (path / "check.py").write_text(exercise["check"])
            (path / "solution.py").write_text(exercise["solution"])
            (path / "solution.py").write_text(exercise["solution"])
            (path / "meta").write_text(json.dumps(exercise, indent=4))
            (path / "wording.md").write_text(exercise["wording"])
            translatables.append(exercise["wording"])
            translatables.append(exercise["title"])
        next_exercise_page = exercises["next"]
    with open("to_translate.py", "w", encoding="UTF-8") as to_translate:
        for string in translatables:
            to_translate.write(f"_({string!r})\n")


if __name__ == "__main__":
    main()
