from django.conf.urls import url
from . import consumers

websocket_urlpatterns = [
    url(
        r"^ws/exercises/(?P<exercise_id>[0-9]+)/", consumers.ExerciseConsumer.as_asgi()
    ),
]
