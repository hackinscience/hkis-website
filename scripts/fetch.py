"""Fetch exercises from hackinscience API.
"""

import argparse
from getpass import getpass
from pathlib import Path
from functools import lru_cache
import json

import requests


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--password-file")
    parser.add_argument(
        "--endpoint", default="https://www.hackinscience.org/api/exercises/"
    )
    parser.add_argument("--page", default="exercises")
    return parser.parse_args()


def fix_newline_at_end_of_file(text):
    if not text:
        return ""
    if text[-1] != "\n":
        return text + "\n"
    return text


def main():
    args = parse_args()
    if not args.username:
        args.username = input("Username: ")
    if args.password_file:
        args.password = Path(args.password_file).read_text().rstrip("\n")
    elif not args.password:
        args.password = getpass()
    next_exercise_page = args.endpoint

    @lru_cache()
    def get(url):
        return requests.get(url, auth=(args.username, args.password)).json()

    while next_exercise_page:
        exercises = get(next_exercise_page)
        if "results" not in exercises:
            print(exercises)
            exit(1)
        for exercise in exercises["results"]:
            if exercise["category"] is not None:
                category = get(exercise["category"])["slug"]
            else:
                category = "exercises"
            page = get(exercise["page"])
            if page["slug"] != args.page:
                continue
            path = Path(category) / exercise["slug"]
            path.mkdir(exist_ok=True, parents=True)
            del exercise["wording"]  # Only use _en and _fr.
            print("Downloading", exercise["title"])
            for file in (
                "check.py",
                "solution.py",
                "pre_check.py",
                "wording_en.md",
                "wording_fr.md",
                "initial_solution.py",
            ):
                (path / file).write_text(
                    fix_newline_at_end_of_file(exercise[file.split(".")[0]]).replace(
                        "\r\n", "\n"
                    )
                )
                del exercise[file.split(".")[0]]
            (path / "meta").write_text(json.dumps(exercise, indent=4))
        next_exercise_page = exercises.get("next")


if __name__ == "__main__":
    main()
