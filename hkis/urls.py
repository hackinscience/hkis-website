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
from django.urls import path, include
from website.views import (dashboard_view, UpdateProfile, index, ExerciseListView,
        ExerciseDetailView)


favicon_view = lambda request: redirect('/static/favicon.ico', permanent=True)

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('accounts/', include('registration.backends.default.urls')),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('exercises', ExerciseListView.as_view(), name='exercises'),
    path('favicon.ico', favicon_view),
    path('exercise/<int:pk>', ExerciseDetailView.as_view(), name='exercise'),
    path('profile/<int:pk>', UpdateProfile.as_view(), name='profile'),
]
