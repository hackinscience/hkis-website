from django.test import TestCase
from django.contrib.auth.models import User


class TestViews(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.client.force_login(User.objects.get(username="a-superuser"))

    def test_get_profile(self):
        self.client.get("/profile/1")

    def test_get_teams(self):
        self.client.get("/teams/")
        self.client.get("/teams/team-mdk")
        self.client.get("/teams/team-mdk/stats")

    def test_get_page(self):
        self.client.get("/")
        self.client.get("/exercises/")
        self.client.get("/help/")

    def test_get_exercise(self):
        self.client.get("/exercises/hello-world")

    def test_get_solution(self):
        self.client.get("/exercises/hello-world/solutions")
