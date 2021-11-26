from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r"^ws/exercises/(?P<exercise_id>[0-9]+)/", consumers.ExerciseConsumer.as_asgi()
    ),
]
