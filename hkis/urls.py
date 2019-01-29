"""hkis URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.conf import settings
from django.urls import path, include
from website.api import router
from website.views import (
    ExerciseListView,
    ExerciseView,
    LessonListView,
    LessonView,
    ProfileView,
    StatsDetailView,
    StatsListView,
    about,
    chat,
    dashboard_view,
    events,
    index,
    privacy,
    team,
)


favicon_view = lambda request: redirect("/static/favicon.ico", permanent=True)

urlpatterns = [
    path("", index, name="index"),
    path("about/", about, name="about"),
    path("team/", team, name="team"),
    path("events/", events, name="events"),
    path("privacy/", privacy, name="privacy"),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("accounts/", include("registration.backends.default.urls")),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("exercises/", ExerciseListView.as_view(), name="exercises"),
    path("exercises/<slug:slug>", ExerciseView.as_view(), name="exercise"),
    path("favicon.ico", favicon_view),
    path("profile/<int:pk>", ProfileView.as_view(), name="profile"),
    path("stats/", StatsListView.as_view(), name="stats"),
    path("stats/<int:pk>", StatsDetailView.as_view(), name="stats"),
    path("chat/", chat, name="chat"),
    path("lessons/", LessonListView.as_view(), name="lesson"),
    path("lessons/<slug:slug>", LessonView.as_view(), name="lesson"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
