# How to contribute


## Requirements

This project requires Python 3.6 at least.


## Install

```
pip install -r requirements.txt
./manage.py migrate
./manage.py loaddata initial  # To get some users and exercises
# (Initial data can be updated using: ./manage.py dumpdata > website/fixtures/initial.json)
./manage.py createsuperuser
./manage.py runserver
```

Install and run a redis server.

You'll maybe need a moulinette running too, currently in the
for_django branch of the moulinette, install firejail, and start it using:

    ./server.py http://127.0.0.1:8000/api/ --verbose --auth staff_login:staff_password


## Translations

```
$ django-admin makemessages -a
# Edit the .po files
$ django-admin compilemessages
```

To translate exercises you'll need to fetch them via the API first:

```
$ pip install requests
$ mkdir -p locale/fr/LC_MESSAGES/
$ python scripts/fetch.py --endpoint https://www.hackinscience.org/api/exercises/
$ python scripts/pygettext.py -o locale/fr/LC_MESSAGES/django.pot to_translate.py
$ cd locale/fr/LC_MESSAGES
$ if [ -f django.po ] ; then msgmerge -U django.po django.pot; else cp django.pot django.po; fi
# msgfmt django.po -o django.mo
```


# TODO

- In the exercise page, links to documentation should open in a new tab.
