from inspect import getsource

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework.test import force_authenticate
from website.models import User


def good_checker_code_for_hello_world():
    from subprocess import run, PIPE

    stdout = run(["python3", "solution.py"], stdout=PIPE, encoding="UTF-8").stdout
    if "hello world" in stdout.lower():
        print("Yeah, well done!")
        exit(0)
    print("Oh now, I don't see Hello World in your output")
    exit(1)


def too_nice_checker_for_hello_world():
    print("Yeah, good answer ♥ bravo!")


def not_too_nice_checker_for_hello_world():
    print("Naupe, you're wrong.")
    exit(1)


class TestAPITestCheck(APITestCase):
    fixtures = ["initial"]

    def setUp(self):
        user = User.objects.get(username="mdk")
        self.client.force_authenticate(user=user)

    def test_good_checker(self):
        response = self.client.post(
            "/test-check/?exercise=1",
            content_type="text/plain",
            data=getsource(good_checker_code_for_hello_world)
            + "good_checker_code_for_hello_world()",
        )
        data = response.json()
        assert not data["false_negatives"]
        assert not data["false_positives"]

    def test_too_nice_checker(self):
        response = self.client.post(
            "/test-check/?exercise=1",
            content_type="text/plain",
            data=getsource(too_nice_checker_for_hello_world)
            + "too_nice_checker_for_hello_world()",
        )
        data = response.json()
        assert not data["false_negatives"]
        assert data["false_positives"]

    def test_not_too_nice_checker(self):
        response = self.client.post(
            "/test-check/?exercise=1",
            content_type="text/plain",
            data=getsource(not_too_nice_checker_for_hello_world)
            + "not_too_nice_checker_for_hello_world()",
        )
        data = response.json()
        assert data["false_negatives"]
        assert not data["false_positives"]
