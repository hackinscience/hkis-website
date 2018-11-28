from django.conf.urls import url
from . import consumers

websocket_urlpatterns = [
    url(
        r"^ws/answers/(?P<user_id>[0-9]+)/(?P<exercise_id>[0-9]+)/$",
        consumers.AnswerConsumer,
    )
]
