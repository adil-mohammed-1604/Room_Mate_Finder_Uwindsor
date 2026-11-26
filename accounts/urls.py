# Owner: Nazim Ali Firdous
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import StyledAuthenticationForm, StyledPasswordResetForm, StyledSetPasswordForm

# Values passed to the password reset email templates (change them in settings.py)
RESET_EMAIL_CONTEXT = {
    "brand_name": settings.SITE_NAME,
    "support_email": settings.SUPPORT_EMAIL,
    "expiry_hours": settings.PASSWORD_RESET_TIMEOUT // 3600,
}

urlpatterns = [
    # Django's built-in views, using our styled forms and branded email templates.
    # These come before django.contrib.auth.urls in roommate_finder/urls.py.
    path(
        "login/",
        auth_views.LoginView.as_view(
            authentication_form=StyledAuthenticationForm, redirect_authenticated_user=True
        ),
        name="login",
    ),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            form_class=StyledPasswordResetForm,
            html_email_template_name="registration/password_reset_email_html.html",
            extra_email_context=RESET_EMAIL_CONTEXT,
        ),
        name="password_reset",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(form_class=StyledSetPasswordForm),
        name="password_reset_confirm",
    ),
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("profile/create/", views.profile_create, name="profile_create"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/delete/", views.profile_delete, name="profile_delete"),
    path("verify/", views.verify_upload, name="verify_upload"),
    path("documents/<int:pk>/", views.private_document, name="private_document"),
]
