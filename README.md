# HackInScience

## Setup

First `firejail` and `redis` (from your package manager), like:

    apt install firejail redis

Install the dependencies:

    python -m pip install requirements.txt

Then run the classical Django things:

    ./manage.py migrate
    ./manage.py loaddata initial
    ./manage.py compilemessages --ignore '.tox' --ignore '.venv'
    ./manage.py createsuperuser

Then in two distinct terminals, or by detaching one of them:

    ./manage.py correction_bot

and:

    ./manage.py runserver


Now you can login to `/admin`, from here you can change everything
about your installation: manage users, create pages, create exercises,
teams, review answers, and so on.

A `/exercises` page, and a `/help` page has been created automatically
for you, you may want to start by adding some exercises to the
`exercises` page.

Alternatively, one can use the `hkis` app alone, in order to
personalize registration, urls, and so on, for this you can install
hkis as a django app in your own project:

    pip install django-hkis


## The pages

A page is literaly a URL in your site, it can contain text (stored
Markdown) and/or exercises.

For example the automatically created page at `/help` is aimed to
store text but no exercises, and the page at `/exercises` is aimed to
present some exercises, maybe after an intro text, or without any
text.

You can live with only those two pages, or create a whole set of pages
like one exercise page per programming language, or per topic, per
student class, ...

Once logged, the users are redirected to the first page (the one with
the smallsest `position`).


## The categories

Inside a page, you can optionally group exercises in categories,
instead of displaying them as a whole single big list. It becomes
handy around 50~70 exercises.


# How to contribute


## Updating the intial fixture

To save the initial.json file, use:

    ./manage.py dumpdata --indent 4 -e admin -e auth.Permission -e contenttypes -e sessions -o hkis/fixtures/initial.json


## Translations

Templates are translated using django `makemessages` and `compilemessages` commands:

```
$ ./manage.py makemessages --locale fr
$ ./manage.py makemessages --locale fr --domain djangojs
# Edit the .po files
$ ./manage.py compilemessages --ignore '.tox' --ignore '.venv'
```

Exercises (title and wording) are translated via the admin (or the
API), we use django-modeltranslation.


## How does the checker bot work?

The answers are load-balanced to correction workers using Celery, so
you can have multiple machines dedicated to correct loads of answers.

Once received by a worker the worker runs two things:

- An optional `pre_check.py` script, that sets-up anything specific
  for this answers (required files and directories, translations,
  whatever is needed).

- A `check.py` script is then started in a sandbox (no internet
  connectivity, restricted filesystem, CPU, memory usage, …).
  This is the script that check the student answer, the protocol is
  simple: if the script exits with non-zero, then then answer is
  wrong. And what's been printed (both stdout and stderr) is
  displayed, as Markdown, to the student. If the answer is right and
  nothing is printed, a default congratulation message is used.

Both `pre_check.py` and `check.py` are in Python, but they're not
limited to check for Python answers, if you want to check for shell
script or C, or whatever, the `check.py` can use `subprocess` to run
the answer script, or compile the answer code, or whatever needed.
