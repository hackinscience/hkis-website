from django.conf import settings
from website.models import Page


def version(request):
    return {"version": settings.GIT_HEAD}


def menu(request):
    return {"pages": Page.objects.order_by("position").filter(in_menu=True)}
