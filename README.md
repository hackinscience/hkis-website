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

To also run the moulinette, you'll need to install `firejail` and `redis` then run:

```
celery -A hkis worker
```


## Translations

Templates are translated using django `makemessages` and `compilemessages` commands:

```
$ django-admin makemessages -a
# Edit the .po files
$ django-admin compilemessages
```

Exercises (title and wording) are translated via the admin (or the
API), we use django-modeltranslation.
