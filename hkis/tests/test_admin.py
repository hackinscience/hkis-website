from django.test import TestCase

from django.contrib.auth.models import User


class TestAdminSuperUser(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.client.force_login(User.objects.get(username="a-superuser"))

    def test_get_admin_exercises(self):
        response = self.client.get("/admin/hkis/exercise/")
        assert b"Hello World" in response.content

    def test_get_admin_exercises_1(self):
        response = self.client.get("/admin/hkis/exercise/1/change/")
        assert b"Hello World" in response.content
