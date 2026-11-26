"""Describes every screen of the staff panel.

To add a table to the panel, add one entry to CONFIG (and, if you like, to SECTIONS
for the sidebar). No view or template code is needed.

Keys: columns, search, filters, fields (editable form fields), readonly (shown above the form),
order (default sort), can_create, can_edit, tabs (field shown as quick tabs above the table),
tab_labels, bulk (extra bulk actions besides delete), avatar (show initials in the first column).
"""
from django.utils.translation import gettext_lazy as _

from accounts.models import LifestylePreference, User, VerificationDocument
from matches.models import ContactMessage, FAQItem, InfoPage, RoommateRequest, TeamMember, VisitLog
from profiles.models import Area, Profile, SavedProfile

# Sidebar groups: (heading, [slugs])
SECTIONS = [
    (_("People"), ["users", "profiles", "lifestyles"]),
    (_("Moderation"), ["verifications", "messages", "requests"]),
    (_("Site content"), ["about", "team", "faq"]),
    (_("Data"), ["areas", "saved", "visits"]),
]

CONFIG = {
    "users": {
        "model": User, "title": _("Users"), "icon": "bi-person-badge",
        "add": _("Add user"), "edit": _("Edit user"), "delete": _("Delete user"),
        "columns": ["email", "first_name", "last_name", "is_staff", "is_active", "date_joined"],
        "search": ["email", "first_name", "last_name"],
        "filters": ["is_staff", "is_active", "is_superuser"],
        "order": "-date_joined", "can_create": True, "can_edit": True, "avatar": True,
    },
    "profiles": {
        "model": Profile, "title": _("Profiles"), "icon": "bi-person-lines-fill",
        "add": _("Add profile"), "edit": _("Edit profile"), "delete": _("Delete profile"),
        "columns": ["full_name", "user", "program", "budget", "preferred_area", "is_verified", "created_at"],
        "search": ["full_name", "user__email", "program", "bio"],
        "filters": ["preferred_area"],
        "tabs": "is_verified",
        "tab_labels": [("1", _("Verified")), ("0", _("Not verified"))],
        "fields": ["user", "full_name", "program", "bio", "phone", "budget", "preferred_area",
                   "photo", "is_verified"],
        "order": "-created_at", "can_create": True, "can_edit": True, "avatar": True,
    },
    "lifestyles": {
        "model": LifestylePreference, "title": _("Lifestyle preferences"), "icon": "bi-moon-stars",
        "add": _("Add lifestyle preference"), "edit": _("Edit lifestyle preference"),
        "delete": _("Delete lifestyle preference"),
        "columns": ["profile", "sleep_schedule", "cleanliness", "pets", "smoking", "guests_often"],
        "search": ["profile__full_name", "profile__user__email"],
        "filters": ["sleep_schedule", "pets", "smoking"],
        "fields": ["profile", "sleep_schedule", "cleanliness", "pets", "smoking", "guests_often"],
        "order": "profile__full_name", "can_create": True, "can_edit": True,
    },
    "verifications": {
        "model": VerificationDocument, "title": _("Verification"), "icon": "bi-patch-check",
        "add": _("Add verification"), "edit": _("Review verification"), "delete": _("Delete verification"),
        "columns": ["profile", "status", "uploaded_at", "reviewed_at", "admin_notes"],
        "search": ["profile__full_name", "profile__user__email"],
        "filters": [],
        "tabs": "status",
        "fields": ["status", "admin_notes"],
        "readonly": ["profile", "uploaded_at", "reviewed_at"],
        "bulk": ["approve", "reject"],
        "order": "-uploaded_at", "can_create": False, "can_edit": True,
    },
    "messages": {
        "model": ContactMessage, "title": _("Contact messages"), "icon": "bi-envelope",
        "add": _("Add message"), "edit": _("Open message"), "delete": _("Delete message"),
        "columns": ["name", "email", "subject", "created_at", "is_resolved"],
        "search": ["name", "email", "subject", "message"],
        "filters": [],
        "tabs": "is_resolved",
        "tab_labels": [("0", _("Open")), ("1", _("Resolved"))],
        "fields": ["is_resolved"],
        "readonly": ["name", "email", "subject", "message", "created_at"],
        "bulk": ["resolve", "reopen"],
        "order": "-created_at", "can_create": False, "can_edit": True, "avatar": True,
    },
    "requests": {
        "model": RoommateRequest, "title": _("Roommate requests"), "icon": "bi-people",
        "add": _("Add request"), "edit": _("Edit request"), "delete": _("Delete request"),
        "columns": ["sender", "receiver", "status", "created_at", "responded_at"],
        "search": ["sender__email", "receiver__email", "message"],
        "filters": [],
        "tabs": "status",
        "fields": ["status"],
        "readonly": ["sender", "receiver", "message", "created_at", "responded_at"],
        "order": "-created_at", "can_create": False, "can_edit": True,
    },
    "about": {
        "model": InfoPage, "title": _("About page"), "icon": "bi-info-circle",
        "add": _("Add page"), "edit": _("Edit About page"), "delete": _("Delete page"),
        "columns": ["title", "slug", "updated_at"],
        "search": ["title", "body"], "filters": [],
        "fields": ["title", "title_fr", "body", "body_fr"],
        "readonly": ["slug"],
        "order": "slug", "can_create": False, "can_edit": True,
    },
    "team": {
        "model": TeamMember, "title": _("Team members"), "icon": "bi-people-fill",
        "add": _("Add team member"), "edit": _("Edit team member"), "delete": _("Delete team member"),
        "columns": ["name", "role", "order", "is_active"],
        "search": ["name", "role"], "filters": [],
        "fields": ["name", "role", "role_fr", "order", "is_active"],
        "order": "order", "can_create": True, "can_edit": True, "avatar": True,
    },
    "faq": {
        "model": FAQItem, "title": _("FAQ"), "icon": "bi-question-circle",
        "add": _("Add question"), "edit": _("Edit question"), "delete": _("Delete question"),
        "columns": ["question", "order", "is_published"],
        "search": ["question", "answer"], "filters": [],
        "fields": ["question", "question_fr", "answer", "answer_fr", "order", "is_published"],
        "order": "order", "can_create": True, "can_edit": True,
    },
    "areas": {
        "model": Area, "title": _("Areas"), "icon": "bi-geo-alt",
        "add": _("Add area"), "edit": _("Edit area"), "delete": _("Delete area"),
        "columns": ["name", "description"],
        "search": ["name", "description"], "filters": [],
        "fields": ["name", "description"],
        "order": "name", "can_create": True, "can_edit": True,
    },
    "saved": {
        "model": SavedProfile, "title": _("Shortlists"), "icon": "bi-bookmark-heart",
        "add": _("Add shortlist entry"), "edit": _("Edit shortlist entry"),
        "delete": _("Delete shortlist entry"),
        "columns": ["user", "profile", "saved_at"],
        "search": ["user__email", "profile__full_name"], "filters": [],
        "order": "-saved_at", "can_create": False, "can_edit": False,
    },
    "visits": {
        "model": VisitLog, "title": _("Visit log"), "icon": "bi-clock-history",
        "add": _("Add visit"), "edit": _("Edit visit"), "delete": _("Delete visit"),
        "columns": ["user", "path", "visited_at"],
        "search": ["user__email", "path"], "filters": [],
        "order": "-visited_at", "can_create": False, "can_edit": False,
    },
}
