# Owner: Nazim Ali Firdous
# Planned models: LifestylePreference, VerificationDocument
from django.db import models

# Owner: Nazim Ali Firdous
import os

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .storage import get_private_storage


class UserManager(BaseUserManager):
    """Creates users that are identified by their email address (there is no username)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email).strip().lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
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
        return self.get(email__iexact=email)


class User(AbstractUser):
    """The account of a student or admin. The email address is the login."""

    username = None
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


def validate_id_file(f):
    ext = os.path.splitext(f.name)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png", ".pdf"):
        raise ValidationError(_("Only JPG, PNG or PDF files are allowed."))
    if f.size > 5 * 1024 * 1024:
        raise ValidationError(_("File too large (max 5 MB)."))


class LifestylePreference(models.Model):
    SLEEP = [("early", _("Early bird")), ("night", _("Night owl")), ("flexible", _("Flexible"))]
    PETS = [("has", _("Have pets")), ("ok", _("Fine with pets")), ("no", _("No pets"))]
    YES_NO = [("yes", _("Yes")), ("no", _("No"))]

    profile = models.OneToOneField(
        "profiles.Profile", on_delete=models.CASCADE, related_name="lifestyle"
    )
    sleep_schedule = models.CharField(max_length=10, choices=SLEEP, default="flexible")
    cleanliness = models.PositiveSmallIntegerField(
        default=3, help_text=_("1 = relaxed, 5 = very tidy")
    )
    pets = models.CharField(max_length=5, choices=PETS, default="ok")
    smoking = models.CharField(max_length=3, choices=YES_NO, default="no")
    guests_often = models.CharField(max_length=3, choices=YES_NO, default="no")

    def clean(self):
        if not 1 <= self.cleanliness <= 5:
            raise ValidationError({"cleanliness": _("Must be between 1 and 5.")})

    def __str__(self):
        return f"Lifestyle of {self.profile}"


class VerificationDocument(models.Model):
    STATUS = [("pending", _("Pending")), ("approved", _("Approved")), ("rejected", _("Rejected"))]

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