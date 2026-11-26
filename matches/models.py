# Owner: Alyan Khowaja
# Planned models: RoommateRequest, VisitLog, ContactMessage
from django.db import models

# Owner: Alyan Khowaja
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class RoommateRequest(models.Model):
    STATUS = [
        ("pending", _("Pending")),
        ("accepted", _("Accepted")),
        ("declined", _("Declined")),
        ("withdrawn", _("Withdrawn")),
    ]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_requests"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_requests"
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(sender=models.F("receiver")), name="no_self_request"
            ),
            models.UniqueConstraint(
                fields=["sender", "receiver"],
                condition=models.Q(status__in=["pending", "accepted"]),
                name="unique_active_request",
            ),
        ]

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"


class VisitLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name="visits",
    )
    session_key = models.CharField(max_length=40, blank=True)
    path = models.CharField(max_length=255)
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visited_at"]

    def __str__(self):
        return f"{self.user or 'guest'} visited {self.path}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} from {self.name}"