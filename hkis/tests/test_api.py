from django.contrib.auth.models import Permission, User, Group
from django.test import TestCase
from rest_framework.test import APITestCase


class TestAPIAnswerAnonymous(APITestCase):
    fixtures = ["initial"]

    def test_get_answer(self):
        response = self.client.get("/api/answers/")
        assert response.status_code == 403


class TestAPIAnswerAuthed(APITestCase):
    fixtures = ["initial"]

    def setUp(self):
        user = User.objects.get(username="a-superuser")
        self.client.force_authenticate(user=user)

    def test_get_answer(self):
        response = self.client.get("/api/answers/")
        assert response.status_code == 200
        assert response.json()["results"]
