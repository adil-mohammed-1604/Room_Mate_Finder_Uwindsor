# Owner: Mohammed Adil
"""Compatibility score (0-100) calculated in plain Python, no external APIs."""


from django.utils.translation import gettext as _


def _lifestyle(profile):
    # Returns None if the profile has no lifestyle row
    return getattr(profile, "lifestyle", None)


def score_breakdown(a, b):
    """Return {"score": int, "rows": [...]} explaining how Profile a and Profile b match.

    Every row has a label, points, max, percent (0-100) and a short detail text.
    """
    rows = []

    def add(label, points, maximum, detail):
        rows.append({
            "label": label, "points": points, "max": maximum,
            "percent": round(points / maximum * 100), "detail": detail,
        })

    # Budget (30 pts) and area (15 pts) are always available
    avg = max((a.budget + b.budget) / 2, 1)
    add(_("Budget"), max(0.0, 1 - abs(a.budget - b.budget) / avg) * 30, 30,
        _("$%(a)s vs $%(b)s per month") % {"a": a.budget, "b": b.budget})
    same_area = bool(a.preferred_area_id and a.preferred_area_id == b.preferred_area_id)
    add(_("Preferred area"), 15 if same_area else 0, 15,
        _("%(a)s vs %(b)s") % {"a": a.preferred_area or _("Any"), "b": b.preferred_area or _("Any")})

    la, lb = _lifestyle(a), _lifestyle(b)
    if la and lb:
        # Sleep schedule (20)
        if la.sleep_schedule == lb.sleep_schedule:
            sleep = 20
        elif "flexible" in (la.sleep_schedule, lb.sleep_schedule):
            sleep = 12
        else:
            sleep = 0
        add(_("Sleep schedule"), sleep, 20,
            _("%(a)s vs %(b)s") % {"a": la.get_sleep_schedule_display(), "b": lb.get_sleep_schedule_display()})
        # Cleanliness (15)
        add(_("Cleanliness"), max(0, 1 - abs(la.cleanliness - lb.cleanliness) / 4) * 15, 15,
            _("%(a)s vs %(b)s") % {"a": f"{la.cleanliness}/5", "b": f"{lb.cleanliness}/5"})
        # Pets (10): only a clash if one has pets and the other doesn't want them
        clash = {la.pets, lb.pets} == {"has", "no"}
        add(_("Pets"), 0 if clash else 10, 10,
            _("%(a)s vs %(b)s") % {"a": la.get_pets_display(), "b": lb.get_pets_display()})
        # Smoking (5) and guests (5)
        add(_("Smoking"), 5 if la.smoking == lb.smoking else 0, 5,
            _("%(a)s vs %(b)s") % {"a": la.get_smoking_display(), "b": lb.get_smoking_display()})
        add(_("Guests"), 5 if la.guests_often == lb.guests_often else 0, 5,
            _("%(a)s vs %(b)s") % {"a": la.get_guests_often_display(), "b": lb.get_guests_often_display()})

    points = sum(r["points"] for r in rows)
    max_points = sum(r["max"] for r in rows)
    return {"score": round(points / max_points * 100), "rows": rows}


def compatibility_score(a, b):
    """Return an integer percentage showing how well Profile a and Profile b match."""
    return score_breakdown(a, b)["score"]
