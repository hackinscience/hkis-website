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


# TODO

- In the exercise page, links to documentation should open in a new tab.
