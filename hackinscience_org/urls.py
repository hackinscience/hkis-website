"""hkis URL Configuration."""
import debug_toolbar
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("accounts/", include("registration.backends.simple.urls")),
    path("admin/", admin.site.urls),
    path("__debug__/", include(debug_toolbar.urls)),
    path("", include("hkis.urls")),
]
