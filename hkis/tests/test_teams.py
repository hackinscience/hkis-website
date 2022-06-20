from django.test import TestCase
from django.contrib.auth.models import User

from hkis.models import Team


class TestTeams(TestCase):
    fixtures = ["initial"]

    def test_public_teams(self):
        assert User.objects.get(username="a-superuser").hkis.public_teams()

    def test_team_by_rank(self):
        assert len(list(Team.objects.first().members_by_rank()))
