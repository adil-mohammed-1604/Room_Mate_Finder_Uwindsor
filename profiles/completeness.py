"""Profile completeness meter: a percentage plus a list of what is still missing."""


def profile_completeness(profile):
    lifestyle = getattr(profile, "lifestyle", None)
    checks = [
        # (label, weight, done, url name to fix it)
        ("Name and budget", 20, bool(profile.full_name and profile.budget), "profile_edit"),
        ("Profile photo", 15, bool(profile.photo), "profile_edit"),
        ("Short bio", 15, bool(profile.bio.strip()), "profile_edit"),
        ("Program of study", 10, bool(profile.program.strip()), "profile_edit"),
        ("Phone number", 10, bool(profile.phone.strip()), "profile_edit"),
        ("Preferred area", 10, bool(profile.preferred_area_id), "profile_edit"),
        ("Lifestyle answers", 10, lifestyle is not None, "profile_edit"),
        ("Verified student ID", 10, bool(profile.is_verified), "verify_upload"),
    ]
    percent = sum(weight for _, weight, done, _ in checks if done)
    missing = [{"label": label, "url_name": url} for label, _, done, url in checks if not done]
    return {"percent": percent, "missing": missing}
