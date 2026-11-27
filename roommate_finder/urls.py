"""Main URL configuration for RoomMate Finder.

Each app has its own urls.py, so team members can add routes
without editing this file (which helps avoid merge conflicts).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("manage/", include("panel.urls")),
    path("admin/", admin.site.urls),
    # Our own login, signup, logout and password reset views (see accounts/views.py)
    path("accounts/", include("accounts.urls")),
    path("matches/", include("matches.urls")),
    path("", include("profiles.urls")),
]

# Serve uploaded files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
