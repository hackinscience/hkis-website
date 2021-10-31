"""hkis URL Configuration."""
import debug_toolbar
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.views.i18n import JavaScriptCatalog

from website.api import router
import website.views as views

urlpatterns = [
    path("", views.index, name="index"),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("page/<slug:url>", views.old_page, name="oldpage"),
    path("teams/", views.teams, name="teams"),
    path("teams/<slug:slug>", views.team_view, name="team"),
    path("teams/<slug:slug>/stats", views.team_stats, name="team_stats"),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("accounts/", include("registration.backends.simple.urls")),
    path("profile/<int:pk>", views.ProfileView.as_view(), name="profile"),
    path("leaderboard/", views.Leaderboard.as_view(), name="leaderboard"),
    path("<slug:page>/", views.PageView.as_view(), name="page"),
    path("<slug:page>/<slug:exercise>", views.ExerciseView.as_view(), name="exercise"),
    path(
        "<slug:page>/<slug:exercise>/solutions",
        views.SolutionView.as_view(),
        name="solutions",
    ),
    path(
        "favicon.ico", lambda request: redirect("/static/favicon.png", permanent=True)
    ),
    path("__debug__/", include(debug_toolbar.urls)),
]
