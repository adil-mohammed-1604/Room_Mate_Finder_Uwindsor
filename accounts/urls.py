# Owner: Nazim Ali Firdous
from django.urls import path

from . import views

urlpatterns = [
    # Our own authentication views (accounts/views.py)
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password_reset/", views.password_reset_view, name="password_reset"),
    path("password_reset/done/", views.password_reset_done_view, name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.password_reset_confirm_view, name="password_reset_confirm"),
    path("reset/done/", views.password_reset_complete_view, name="password_reset_complete"),
    # Profile and verification
    path("profile/create/", views.profile_create, name="profile_create"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/delete/", views.profile_delete, name="profile_delete"),
    path("verify/", views.verify_upload, name="verify_upload"),
    path("documents/<int:pk>/", views.private_document, name="private_document"),
]
