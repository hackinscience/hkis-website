"""HackInScience CLI.

This can be used to do HackInScience exercises without a web browser:

    $ hkis login
    Username: ...
    Password: ...

    $ hkis list
    ✓ 	1. Hello World 	            Résolu 11589 fois
    ✓ 	2. Print 42 	            Résolu 11442 fois
    ✓ 	3. Secondes dans une année  Résolu 3288 fois
    ✓ 	4. Using operators 	    Résolu 6525 fois
    ✓ 	5. Characters counting 	    Résolu 8289 fois
    ✓ 	6. Les nombres carrés 	    Résolu 2679 fois
    ✓ 	7. Powers of two 	    Résolu 6817 fois
    ✓ 	8. Comparisons 	            Résolu 5952 fois
    ✓ 	9. Import 	            Résolu 5369 fois
    ✓ 	10. Counting Words          Résolu 4937 fois

    $ hkis get Hello World
    Downloaded hello-world.py, check using:

        hkis check hello-world.py

"""
import argparse
import getpass
from pathlib import Path
import json
import configparser
import sys
from textwrap import indent

import tabulate
import requests
from websocket import create_connection

__version__ = "0.1"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers()
    login_parser = subparsers.add_parser("login")
    login_parser.set_defaults(func=hkis_login)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(func=hkis_list)

    get_parser = subparsers.add_parser("get")
    get_parser.set_defaults(func=hkis_get)
    get_parser.add_argument("name", nargs="+", help="Exercise name")

    check_parser = subparsers.add_parser("check")
    check_parser.set_defaults(func=hkis_check)
    check_parser.add_argument("exercise_path", type=Path, help="File to check")

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    return args


def get_config():
    config_file = Path("~/.hkis.conf").expanduser()
    config_file.touch()
    config_file.chmod(0o600)
    config = configparser.RawConfigParser()
    config.config_file = config_file
    config.read(config_file)
    return config


def hkis_login(config, session):
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    config["hackinscience.org"] = {"username": username, "password": password}
    with open(config.config_file, "w", encoding="UTF-8") as configfile:
        config.write(configfile)


def hkis_list(config, session):
    table = []
    exercises = session.get("https://www.hackinscience.org/api/exercises/").json()
    for exercise in exercises["results"]:
        table.append([exercise["title"]])
    print(tabulate.tabulate(table))


def find_exercise(session, name):
    exercises = session.get("https://www.hackinscience.org/api/exercises/").json()
    for exercise in exercises["results"]:
        if name == exercise["title"]:
            full_exercise = session.get(exercise["url"]).json()
            full_exercise["id"] = full_exercise["url"].split("/")[-2]
            return full_exercise
    raise ValueError("Cannot find exercise " + name)


def hkis_get(config, session, name):
    name = " ".join(name)
    exercise = find_exercise(session, name)
    exercise_path = exercise["slug"] + ".py"
    with open(exercise_path, "w", encoding="UTF-8") as exercise_file:
        exercise_file.write("# " + exercise["title"] + "\n\n")
        exercise_file.write(indent(exercise["wording_en"], "# ", lambda l: True))
        exercise_file.write("\n\n")
        exercise_file.write(exercise["initial_solution"])
    print(
        f"Downloaded {exercise_path}, you can upload it back using:",
        f"    hkis check {exercise_path}",
        sep="\n\n",
    )


def hkis_check(config, session, exercise_path):
    def dot():
        print(".", end="")
        sys.stdout.flush()

    source_code = exercise_path.read_text(encoding="UTF-8")
    title = source_code.splitlines()[0].lstrip("#").strip()
    exercise = find_exercise(session, title)
    endpoint = f"wss://www.hackinscience.org/ws/exercises/{exercise['id']}/"
    dot()
    ws = create_connection(endpoint)
    dot()
    ws.send(json.dumps({"type": "answer", "source_code": source_code}))
    while True:
        dot()
        result = json.loads(ws.recv())
        if result["is_corrected"]:
            print("\n", result["correction_message"])
            break
    ws.close()


def main():
    args = vars(parse_args())
    config = get_config()
    with requests.Session() as session:
        session.auth = (
            config["hackinscience.org"]["username"],
            config["hackinscience.org"]["password"],
        )
        func = args.pop("func")
        func(config, session, **args)


if __name__ == "__main__":
    main()
