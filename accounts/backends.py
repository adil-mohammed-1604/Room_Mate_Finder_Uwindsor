# Owner: Nazim Ali Firdous
"""Our own login check: find the user by email and compare the password hash."""
from django.contrib.auth.backends import ModelBackend

from .models import User, UserManager


class EmailBackend(ModelBackend):
    """Authenticates with an email address and password.

    Accepts the email as `email=` (our login view) or `username=` (the Django admin
    login and the test client both send it under that name). Permission checks
    (has_perm) are inherited from ModelBackend so the admin keeps working.
    """

    def authenticate(self, request, email=None, password=None, username=None, **kwargs):
        email = UserManager.clean_email(email or username)
        if not email or password is None:
            return None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            User().set_password(password)  # same work as a real check, so timing doesn't reveal emails
            return None
        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if user.is_active else None
