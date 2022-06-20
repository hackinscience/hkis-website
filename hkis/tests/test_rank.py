from django.contrib.auth.models import User
from django.test import TestCase

from hkis.models import UserInfo


class TestRankUserWithInfo(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.user = User.objects.create(username="Temporary")
        self.userinfo, _ = UserInfo.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)

    def test_recompute_rank(self):
        self.userinfo.recompute_points()
        assert UserInfo.with_rank.get(user__username="Temporary").rank == 2

    def test_recompute_ranks(self):
        UserInfo.objects.recompute_points()
        assert UserInfo.with_rank.get(user__username="Temporary").rank == 2


class TestRankUserWithNoInfo(TestCase):
    fixtures = ["initial"]

    def setUp(self):
        self.user = User.objects.create(username="Temporary")

    def test_recompute_ranks(self):
        UserInfo.objects.recompute_points()
