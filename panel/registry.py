"""Describes every screen of the staff panel.

To add a table to the panel, add one entry to CONFIG (and, if you like, to SECTIONS
for the sidebar). No view or template code is needed.

Keys: columns, search, filters, fields (editable form fields), readonly (shown above the form),
order (default sort), can_create, can_edit, tabs (field shown as quick tabs above the table),
tab_labels, bulk (extra bulk actions besides delete), avatar (show initials in the first column).
"""

from accounts.models import LifestylePreference, User, VerificationDocument
from matches.models import ContactMessage, RoommateRequest, VisitLog
from profiles.models import Area, Profile, SavedProfile

# Sidebar groups: (heading, [slugs])
SECTIONS = [
    ("People", ["users", "profiles", "lifestyles"]),
    ("Moderation", ["verifications", "messages", "requests"]),
    ("Data", ["areas", "saved", "visits"]),
]

CONFIG = {
    "users": {
        "model": User, "title": "Users", "icon": "bi-person-badge",
        "add": "Add user", "edit": "Edit user", "delete": "Delete user",
        "columns": ["email", "first_name", "last_name", "is_staff", "is_active", "date_joined"],
        "search": ["email", "first_name", "last_name"],
        "filters": ["is_staff", "is_active", "is_superuser"],
        "order": "-date_joined", "can_create": True, "can_edit": True, "avatar": True,
    },
    "profiles": {
        "model": Profile, "title": "Profiles", "icon": "bi-person-lines-fill",
        "add": "Add profile", "edit": "Edit profile", "delete": "Delete profile",
        "columns": ["full_name", "user", "program", "budget", "preferred_area", "is_verified", "created_at"],
        "search": ["full_name", "user__email", "program", "bio"],
        "filters": ["preferred_area"],
        "tabs": "is_verified",
        "tab_labels": [("1", "Verified"), ("0", "Not verified")],
        "fields": ["user", "full_name", "program", "bio", "phone", "budget", "preferred_area",
                   "photo", "is_verified"],
        "order": "-created_at", "can_create": True, "can_edit": True, "avatar": True,
    },
    "lifestyles": {
        "model": LifestylePreference, "title": "Lifestyle preferences", "icon": "bi-moon-stars",
        "add": "Add lifestyle preference", "edit": "Edit lifestyle preference",
        "delete": "Delete lifestyle preference",
        "columns": ["profile", "sleep_schedule", "cleanliness", "pets", "smoking", "guests_often"],
        "search": ["profile__full_name", "profile__user__email"],
        "filters": ["sleep_schedule", "pets", "smoking"],
        "fields": ["profile", "sleep_schedule", "cleanliness", "pets", "smoking", "guests_often"],
        "order": "profile__full_name", "can_create": True, "can_edit": True,
    },
    "verifications": {
        "model": VerificationDocument, "title": "Verification", "icon": "bi-patch-check",
        "add": "Add verification", "edit": "Review verification", "delete": "Delete verification",
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
        "model": ContactMessage, "title": "Contact messages", "icon": "bi-envelope",
        "add": "Add message", "edit": "Open message", "delete": "Delete message",
        "columns": ["name", "email", "subject", "created_at", "is_resolved"],
        "search": ["name", "email", "subject", "message"],
        "filters": [],
        "tabs": "is_resolved",
        "tab_labels": [("0", "Open"), ("1", "Resolved")],
        "fields": ["is_resolved"],
        "readonly": ["name", "email", "subject", "message", "created_at"],
        "bulk": ["resolve", "reopen"],
        "order": "-created_at", "can_create": False, "can_edit": True, "avatar": True,
    },
    "requests": {
        "model": RoommateRequest, "title": "Roommate requests", "icon": "bi-people",
        "add": "Add request", "edit": "Edit request", "delete": "Delete request",
        "columns": ["sender", "receiver", "status", "created_at", "responded_at"],
        "search": ["sender__email", "receiver__email", "message"],
        "filters": [],
        "tabs": "status",
        "fields": ["status"],
        "readonly": ["sender", "receiver", "message", "created_at", "responded_at"],
        "order": "-created_at", "can_create": False, "can_edit": True,
    },
    "areas": {
        "model": Area, "title": "Areas", "icon": "bi-geo-alt",
        "add": "Add area", "edit": "Edit area", "delete": "Delete area",
        "columns": ["name", "description"],
        "search": ["name", "description"], "filters": [],
        "fields": ["name", "description"],
        "order": "name", "can_create": True, "can_edit": True,
    },
    "saved": {
        "model": SavedProfile, "title": "Shortlists", "icon": "bi-bookmark-heart",
        "add": "Add shortlist entry", "edit": "Edit shortlist entry",
        "delete": "Delete shortlist entry",
        "columns": ["user", "profile", "saved_at"],
        "search": ["user__email", "profile__full_name"], "filters": [],
        "order": "-saved_at", "can_create": False, "can_edit": False,
    },
    "visits": {
        "model": VisitLog, "title": "Visit log", "icon": "bi-clock-history",
        "add": "Add visit", "edit": "Edit visit", "delete": "Delete visit",
        "columns": ["user", "path", "visited_at"],
        "search": ["user__email", "path"], "filters": [],
        "order": "-visited_at", "can_create": False, "can_edit": False,
    },
}
