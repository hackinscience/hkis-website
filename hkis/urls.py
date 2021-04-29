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
import website.views as views

urlpatterns = [
    path("", views.index, name="index"),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("page/<slug:url>", views.old_page, name="oldpage"),
    path("teams/", views.teams, name="teams"),
    path("teams/<slug:slug>", views.team, name="team"),
    path("teams/<slug:slug>/stats", views.team_stats, name="team_stats"),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
    path("accounts/", include("registration.backends.simple.urls")),
    path("<slug:page>/", views.PageView.as_view(), name="page"),
    path("<slug:page>/<slug:exercise>", views.ExerciseView.as_view(), name="exercise"),
    path(
        "<slug:page>/<slug:exercise>/solutions",
        views.SolutionView.as_view(),
        name="solutions",
    ),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    path(
        "favicon.ico", lambda request: redirect("/static/favicon.ico", permanent=True)
    ),
    path("profile/<int:pk>", views.ProfileView.as_view(), name="profile"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
