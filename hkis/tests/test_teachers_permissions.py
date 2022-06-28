from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from rest_framework.test import APITestCase

from hkis.models import Exercise, Answer
from hkis.admin import ExerciseAdmin


class MockRequest:
    def __init__(self, user):
        self.user = user


class TestTeachersCanCreateExerciseViaAdmin(TestCase):
    fixtures = ["initial"]

    def test_create_exercise_via_admin(self):
        exercise_admin = ExerciseAdmin(model=Exercise, admin_site=AdminSite())
        a_teacher = User.objects.get(username="a-teacher")
        an_exercise = Exercise(title="Test", page_id=1)
        exercise_admin.save_model(
            obj=an_exercise, request=MockRequest(user=a_teacher), form=None, change=None
        )
        assert Exercise.objects.get(title="Test").category.title == "Sandbox"


class TestTeachersCanCreateExerciseViaAPI(APITestCase):
    fixtures = ["initial"]

    def setUp(self):
        user = User.objects.get(username="a-teacher")
        self.client.force_authenticate(user=user)

    def test_create_exercise_via_api(self):
        response = self.client.post(
            "/api/exercises/", {"title": "Test", "page": "/api/pages/1/"}
        )
        assert response.status_code == 201
        assert b"Test" in self.client.get(response.json()["url"]).content


class TestAdminStaffWithTeacherGroup(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.user = User.objects.get(username="a-teacher")
        self.client.force_login(self.user)

    def test_get_admin_exercises(self):
        response = self.client.get("/admin/hkis/exercise/")
        assert b"Hello World" not in response.content  # mdk's exercise
        assert b"Print 42" in response.content  # Lisa's exercise

    def test_get_admin_exercises_1(self):
        """Exercise 1 is owned by mdk, Lisa can't view it."""
        response = self.client.get("/admin/hkis/exercise/1/change/")
        assert response.status_code == 302

    def test_get_admin_exercises_2(self):
        """Exercise 1 is owned by Lisa, Lisa can view it."""
        response = self.client.get("/admin/hkis/exercise/2/change/")
        assert response.status_code == 200

    def test_create_exercise(self):
        response = self.client.post(
            "/admin/hkis/exercise/add/",
            {"title_en": "Lisa's exercise", "page": 1, "position": 100, "points": 1},
        )
        assert response.status_code == 302
        created = Exercise.objects.get(title="Lisa's exercise")
        assert created.is_published is False  # A staff can't self-publish exercises
        assert created.author == self.user
        assert created.category.title == "Sandbox"  # All new exercises to the sandbox
