"""Profile completeness meter: a percentage plus a list of what is still missing."""
from django.utils.translation import gettext as _


def profile_completeness(profile):
    lifestyle = getattr(profile, "lifestyle", None)
    checks = [
        # (label, weight, done, url name to fix it)
        (_("Name and budget"), 20, bool(profile.full_name and profile.budget), "profile_edit"),
        (_("Profile photo"), 15, bool(profile.photo), "profile_edit"),
        (_("Short bio"), 15, bool(profile.bio.strip()), "profile_edit"),
        (_("Program of study"), 10, bool(profile.program.strip()), "profile_edit"),
        (_("Phone number"), 10, bool(profile.phone.strip()), "profile_edit"),
        (_("Preferred area"), 10, bool(profile.preferred_area_id), "profile_edit"),
        (_("Lifestyle answers"), 10, lifestyle is not None, "profile_edit"),
        (_("Verified student ID"), 10, bool(profile.is_verified), "verify_upload"),
    ]
    percent = sum(weight for _, weight, done, _ in checks if done)
    missing = [{"label": label, "url_name": url} for label, _, done, url in checks if not done]
    return {"percent": percent, "missing": missing}
