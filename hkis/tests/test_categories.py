from django.test import TestCase

from hkis.models import Category


class TestCategories(TestCase):
    fixtures = ["initial"]

    def test_unnamed_category(self):
        c1 = Category.objects.create()
        assert str(c1) == "Unnamed"

    def test_named_category(self):
        assert str(Category.objects.first()) != "Unnamed"
