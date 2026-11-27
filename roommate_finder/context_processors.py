"""Makes the branding values from settings.py available in every template."""
from django.conf import settings


def branding(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
        "DEBUG_MODE": settings.DEBUG,
    }


def site_extras(request):
    """Pending-request count for the navbar badge, and the saved light/dark choice."""
    pending = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        from matches.models import RoommateRequest

        pending = RoommateRequest.objects.filter(receiver=user, status="pending").count()
    theme = request.COOKIES.get("theme", "light")
    return {"pending_requests": pending, "theme": theme if theme in ("light", "dark") else "light"}
