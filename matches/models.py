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
        indexes = [
            models.Index(fields=["receiver", "status"], name="req_receiver_status_idx"),
            models.Index(fields=["sender", "status"], name="req_sender_status_idx"),
        ]
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
        indexes = [
            models.Index(fields=["user", "-visited_at"], name="visit_user_time_idx"),
            models.Index(fields=["visited_at"], name="visit_time_idx"),
        ]

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


def localized(obj, field):
    """Return obj.<field>_fr when French is active and filled in, otherwise obj.<field>."""
    from django.utils import translation

    if translation.get_language() and translation.get_language().startswith("fr"):
        return getattr(obj, f"{field}_fr", "") or getattr(obj, field)
    return getattr(obj, field)


class InfoPage(models.Model):
    """Editable text for the About page (staff edit it in /manage/; French is optional)."""

    slug = models.SlugField(unique=True)
    title = models.CharField(_("Title"), max_length=150)
    title_fr = models.CharField(_("Title (French)"), max_length=150, blank=True)
    body = models.TextField(_("Text"), help_text=_("Separate paragraphs with a blank line."))
    body_fr = models.TextField(_("Text (French)"), blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def display_title(self):
        return localized(self, "title")

    @property
    def paragraphs(self):
        return [p.strip() for p in localized(self, "body").split("\n\n") if p.strip()]


class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(_("Role"), max_length=150)
    role_fr = models.CharField(_("Role (French)"), max_length=150, blank=True)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Shown on the Team page"), default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name

    @property
    def display_role(self):
        return localized(self, "role")


class FAQItem(models.Model):
    question = models.CharField(_("Question"), max_length=255)
    question_fr = models.CharField(_("Question (French)"), max_length=255, blank=True)
    answer = models.TextField(_("Answer"))
    answer_fr = models.TextField(_("Answer (French)"), blank=True)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)
    is_published = models.BooleanField(_("Shown on the FAQ page"), default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "FAQ item"

    def __str__(self):
        return self.question

    @property
    def display_question(self):
        return localized(self, "question")

    @property
    def display_answer(self):
        return localized(self, "answer")
