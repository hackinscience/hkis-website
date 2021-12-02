"""Fetch exercises from hackinscience API.
"""

import argparse
from contextlib import suppress
import json
from functools import lru_cache
from pathlib import Path

import requests

from utils import common_parse_args


def parse_args():
    args, remaining = common_parse_args(__doc__)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--page", help="Only download exercises for the given page slug."
    )
    return parser.parse_args(remaining, args)


def fix_newline_at_end_of_file(text):
    if not text:
        return ""
    if text[-1] != "\n":
        return text + "\n"
    return text


def get_exercises(endpoint, session):
    while endpoint:
        response = session.get(endpoint).json()
        yield from response["results"]
        endpoint = response.get("next")


def main():
    args = parse_args()

    session = requests.session()
    session.auth = (args.username, args.password)

    @lru_cache()
    def get(url):
        return session.get(url).json()

    for exercise in get_exercises(args.endpoint, session):
        exercise = get(exercise["url"])
        if exercise.get("page"):
            page = get(exercise["page"])["slug"]
        else:
            page = "exercises"
        if args.page and page != args.page:
            continue
        path = Path(page) / exercise["slug"]
        path.mkdir(exist_ok=True, parents=True)
        del exercise["wording"]  # Only use _en and _fr.
        del exercise["solved_by"]  # Change everytime :D
        print("Downloading", exercise["title"], "in", page)
        with suppress(FileNotFoundError):
            old_meta = json.loads((path / "meta").read_text(encoding="UTF-8"))
            if old_meta["url"] != exercise["url"]:
                raise RuntimeError(
                    f"Exercise {old_meta['url']} and exercise {exercise['url']} "
                    "have the same slug and are the same page.",
                )
        for file in (
            "check.py",
            "pre_check.py",
            "wording_en.md",
            "wording_fr.md",
            "initial_solution.py",
        ):
            (path / file).write_text(
                fix_newline_at_end_of_file(
                    exercise[file.split(".", maxsplit=1)[0]]
                ).replace("\r\n", "\n")
            )
            del exercise[file.split(".", maxsplit=1)[0]]
        (path / "meta").write_text(json.dumps(exercise, indent=4))


if __name__ == "__main__":
    main()
