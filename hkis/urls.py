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
from django.views.i18n import JavaScriptCatalog
from website.api import router
from website.views import (
    ExerciseListView,
    LeaderBoardView,
    ExerciseView,
    ProfileView,
    SolutionView,
    StatsDetailView,
    StatsListView,
    about,
    sponsor,
    helppage,
    index,
    team,
)


urlpatterns = [
    path("", index, name="index"),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("about/", about, name="about"),
    path("help/", helppage, name="help"),
    path("team/", team, name="team"),
    path("admin/", admin.site.urls),
    path("sponsor/", sponsor, name="sponsor"),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("accounts/", include("registration.backends.simple.urls")),
    path("exercises/", ExerciseListView.as_view(), name="exercises"),
    path("leaderboard/", LeaderBoardView.as_view(), name="leaderboard"),
    path("exercises/<slug:slug>", ExerciseView.as_view(), name="exercise"),
    path("exercises/<slug:slug>/solutions", SolutionView.as_view(), name="solutions"),
    path(
        "favicon.ico", lambda request: redirect("/static/favicon.ico", permanent=True)
    ),
    path("profile/<int:pk>", ProfileView.as_view(), name="profile"),
    path("stats/", StatsListView.as_view(), name="stats"),
    path("stats/<int:pk>", StatsDetailView.as_view(), name="stats"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
