from django.conf import settings


def version(request):
    return {"version": settings.GIT_HEAD}
