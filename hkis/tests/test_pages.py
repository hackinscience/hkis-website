from django.test import TestCase

from hkis.models import Page


class TestPages(TestCase):
    fixtures = ["initial"]

    def test_page(self):
        p1 = Page.objects.first()
        assert p1.slug in p1.get_absolute_url()
