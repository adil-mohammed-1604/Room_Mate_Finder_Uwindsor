# Owner: Nazim Ali Firdous
# Planned models: LifestylePreference, VerificationDocument
from django.db import models

# Owner: Nazim Ali Firdous
import os

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .storage import get_private_storage


class UserManager(BaseUserManager):
    """Creates users that are identified by their email address (there is no username)."""

    use_in_migrations = True

    @staticmethod
    def clean_email(email):
        return (email or "").strip().lower()

    def _create_user(self, email, password, **extra_fields):
        email = self.clean_email(email)
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # stores a salted hash, never the plain password
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_staff=True and is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        # Used when logging in: the email is not case-sensitive
        return self.get(email__iexact=self.clean_email(email))


class User(AbstractBaseUser, PermissionsMixin):
    """Our own account model for students and admins. The email address is the login.

    AbstractBaseUser only gives the password hash and last_login columns; every other
    field below is defined by us. PermissionsMixin adds is_superuser, groups and
    permissions so the Django admin and the staff panel keep working.
    """

    email = models.EmailField("email address", unique=True)
    first_name = models.CharField("first name", max_length=150, blank=True)
    last_name = models.CharField("last name", max_length=150, blank=True)
    is_active = models.BooleanField(
        "active", default=True, help_text="Untick this instead of deleting an account."
    )
    is_staff = models.BooleanField(
        "staff status", default=False, help_text="Can log in to the admin site and staff panel."
    )
    date_joined = models.DateTimeField("date joined", default=timezone.now)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def clean(self):
        super().clean()
        self.email = UserManager.clean_email(self.email)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        return self.first_name or self.email

    def __str__(self):
        return self.email


def validate_id_file(f):
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".pdf"):
        raise ValidationError("Only JPG, PNG or PDF files are allowed.")
    if f.size > 5 * 1024 * 1024:
        raise ValidationError("File too large (max 5 MB).")


class LifestylePreference(models.Model):
    SLEEP = [("early", "Early bird"), ("night", "Night owl"), ("flexible", "Flexible")]
    PETS = [("has", "Have pets"), ("ok", "Fine with pets"), ("no", "No pets")]
    YES_NO = [("yes", "Yes"), ("no", "No")]

    profile = models.OneToOneField(
        "profiles.Profile", on_delete=models.CASCADE, related_name="lifestyle"
    )
    sleep_schedule = models.CharField(max_length=10, choices=SLEEP, default="flexible")
    cleanliness = models.PositiveSmallIntegerField(
        default=3, help_text="1 = relaxed, 5 = very tidy"
    )
    pets = models.CharField(max_length=5, choices=PETS, default="ok")
    smoking = models.CharField(max_length=3, choices=YES_NO, default="no")
    guests_often = models.CharField(max_length=3, choices=YES_NO, default="no")

    def clean(self):
        if not 1 <= self.cleanliness <= 5:
            raise ValidationError({"cleanliness": "Must be between 1 and 5."})

    def __str__(self):
        return f"Lifestyle of {self.profile}"


class VerificationDocument(models.Model):
    STATUS = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]

    profile = models.ForeignKey(
        "profiles.Profile", on_delete=models.CASCADE, related_name="verification_documents"
    )
    student_id = models.FileField(
        upload_to="student_ids/", storage=get_private_storage, validators=[validate_id_file]
    )
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    admin_notes = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.profile} ({self.status})"