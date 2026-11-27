"""Main URL configuration for RoomMate Finder.

Each app has its own urls.py, so team members can add routes
without editing this file (which helps avoid merge conflicts).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # language switch (POST)
    path("manage/", include("panel.urls")),
    path("admin/", admin.site.urls),
    # accounts.urls comes first so its styled login / password reset views
    # win over Django's built-in ones (logout and the rest still come from Django).
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("matches/", include("matches.urls")),
    path("", include("profiles.urls")),
]

# Serve uploaded files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
