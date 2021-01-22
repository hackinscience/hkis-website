# How to use Docker


## Requirements

You need **docker** and **docker-compose**. You have to create a local settings file:

```bash
$ cat hkis/local_settings.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("redis", 6379)]},
    }
}

CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
INTERNAL_IPS = {"celery"}
```

## Build
```bash
$ docker-compose build
```

## First start
```bash
$ docker-compose up
# In another terminal
$ docker-compose run web python manage.py migrate
$ docker-compose run web python manage.py loaddata initial
```

You can create a admin account with:
```bash
$ docker-compose run web python manage.py createsuperuser --username admin --email ad@min.fr
```

## Make locales if needed
```bash
$ docker-compose run web python ./manage.py makemessages --locale fr
$ docker-compose run web python ./manage.py makemessages --locale fr --domain djangojs
# Edit the .po files
$ docker-compose run web python ./manage.py compilemessages
```
