# Owner: Mohammed Adil
# Planned models: Profile, Area, SavedProfile
from django.db import models
# Owner: Mohammed Adil
from django.conf import settings
from django.db import models


class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    full_name = models.CharField(max_length=120)
    program = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)  # shown only after a request is accepted
    budget = models.PositiveIntegerField(help_text="Monthly budget in CAD")
    preferred_area = models.ForeignKey(
        Area, on_delete=models.SET_NULL, null=True, blank=True, related_name="profiles"
    )
    photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name or self.user.email


class SavedProfile(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_profiles"
    )
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-saved_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "profile"], name="unique_saved_profile")
        ]

    def __str__(self):
        return f"{self.user} saved {self.profile}"