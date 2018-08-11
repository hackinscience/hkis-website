#!/usr/bin/env python3

import json
import pytz
import django
from tqdm import tqdm
from datetime import datetime, timezone
from website.models import Exercise, Answer
from django.contrib.auth.models import User
import random

UNUSABLE_PASSWORD_PREFIX = "!"  # This will never be a valid encoded hash
UNUSABLE_PASSWORD_SUFFIX_LENGTH = (
    40
)  # number of random chars to add after UNUSABLE_PASSWORD_PREFIX


def get_random_string(
    length=12,
    allowed_chars="abcdefghijklmnopqrstuvwxyz" "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
):
    """
    Return a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    return "".join(random.choice(allowed_chars) for i in range(length))


# CREATE TABLE IF NOT EXISTS "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
#     "password" varchar(128) NOT NULL,
#     "last_login" datetime NULL,
#     "is_superuser" bool NOT NULL,
#     "username" varchar(150) NOT NULL UNIQUE,
#     "first_name" varchar(30) NOT NULL,
#     "email" varchar(254) NOT NULL,
#     "is_staff" bool NOT NULL,
#     "is_active" bool NOT NULL,
#     "date_joined" datetime NOT NULL,
#     "last_name" varchar(150) NOT NULL);
#
# CREATE TABLE IF NOT EXISTS "website_exercise" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
#     "title" varchar(255) NOT NULL,
#     "check" text NOT NULL,
#     "solution" text NOT NULL,
#     "wording" text NOT NULL);
#
# CREATE TABLE IF NOT EXISTS "website_answer" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
#     "source_code" text NOT NULL,
#     "is_corrected" bool NOT NULL,
#     "is_valid" bool NOT NULL,
#     "correction_message" text NOT NULL,
#     "created_at" datetime NOT NULL,
#     "corrected_at" datetime NULL,
#     "exercise_id" integer NOT NULL REFERENCES "website_exercise" ("id") DEFERRABLE INITIALLY DEFERRED,
#     "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

# In dump:
# ["answer"] contains: ['id', 'user_id', 'exercise_id', 'source', 'isCorrected',
#        'correctionMessage', 'isValid', 'created_at', 'corrected_at']
# ["user"] contains: ['id', 'username', 'username_canonical', 'email', 'email_canonical', 'enabled', 'salt', 'password', 'last_login', 'confirmation_token', 'password_requested_at', 'roles', 'promo', 'is_beta']
# ["exercise"] contains: ['id', 'path', 'title', 'content', 'checks', 'solution']


def now():
    return datetime.now(pytz.utc)


def from_isodate(date):
    if date is None:
        return None
    date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
    date.replace(tzinfo=pytz.utc)
    return date


def save_exercise(from_mysql):
    exercise = Exercise(
        id=from_mysql["id"],
        title=from_mysql["title"],
        check=from_mysql["checks"],
        solution=from_mysql["solution"],
        wording=from_mysql["content"],
    )
    exercise.save()


def save_user(from_mysql):
    user = User(
        id=from_mysql["id"],
        password=UNUSABLE_PASSWORD_PREFIX
        + get_random_string(UNUSABLE_PASSWORD_SUFFIX_LENGTH),
        last_login=None,
        is_superuser=False,
        username=from_mysql["username"],
        first_name=from_mysql["username"],
        email=from_mysql["email"],
        is_staff=False,
        is_active=True,
        date_joined=now(),
        last_name=from_mysql["username"],
    )
    user.save()


def save_answer(from_mysql):
    answer = Answer(
        exercise_id=from_mysql["exercise_id"],
        user_id=from_mysql["user_id"],
        source_code=from_mysql["source"] if from_mysql["source"] is not None else "",
        is_corrected=from_mysql["isCorrected"],
        is_valid=from_mysql["isValid"] if from_mysql["isValid"] is not None else False,
        correction_message=from_mysql["correctionMessage"]
        if from_mysql["correctionMessage"] is not None
        else "",
        created_at=from_isodate(from_mysql["created_at"]),
        corrected_at=from_isodate(from_mysql["corrected_at"]),
    )
    answer.save()


def run():
    known_users = set()
    known_exercises = set()
    with open("dump.json") as f:
        dump = json.load(f)
    for user in tqdm(dump["user"]):
        known_users.add(user["id"])
        save_user(user)
    for exercise in tqdm(dump["exercise"]):
        known_exercises.add(exercise["id"])
        save_exercise(exercise)
    for answer in tqdm(dump["answer"]):
        if answer["user_id"] is None:
            print("Skipping answer", answer)
            continue
        if (
            answer["exercise_id"] in known_exercises
            and answer["user_id"] in known_users
        ):
            try:
                save_answer(answer)
            except django.db.utils.IntegrityError as err:
                print(err)
                print("on", answer)
                exit(0)
