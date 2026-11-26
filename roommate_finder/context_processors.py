"""Makes the branding values from settings.py available in every template."""
from django.conf import settings
from django.utils.translation import gettext

DEFAULT_SITE_THEME = {
    "navy": "#1E3A5F",
    "coral": "#FF6B6B",
    "tint": "#EEF3F8",
    "green": "#2EAD6B",
    "radius": "0.5rem",
    "font": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
}
DEFAULT_FOOTER = {"tagline": "", "location": "", "social": {}, "credit": ""}


def branding(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
        "DEBUG_MODE": settings.DEBUG,
    }


def site_theme(request):
    """SITE_THEME turned into CSS variables, and SITE_FOOTER for the footer template."""
    theme = {**DEFAULT_SITE_THEME, **getattr(settings, "SITE_THEME", {})}
    css_vars = "".join(f"--rf-{key}:{value};" for key, value in theme.items() if key not in ("radius", "font"))
    css_vars += f"--rf-radius:{theme['radius']};--rf-font:{theme['font']};"
    footer = {**DEFAULT_FOOTER, **getattr(settings, "SITE_FOOTER", {})}
    # Texts that have a French version in locale/fr_translations.py are shown in the visitor's language
    footer["tagline"] = gettext(footer["tagline"]) if footer["tagline"] else ""
    footer["credit"] = gettext(footer["credit"]) if footer["credit"] else ""
    social = [(name, url) for name, url in footer["social"].items() if url]
    return {"SITE_CSS_VARS": css_vars, "SITE_FOOTER": footer, "SOCIAL_LINKS": social}


def site_extras(request):
    """Pending-request count for the navbar badge, and the saved light/dark choice."""
    pending = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        from matches.models import RoommateRequest

        pending = RoommateRequest.objects.filter(receiver=user, status="pending").count()
    theme = request.COOKIES.get("theme", "light")
    return {"pending_requests": pending, "theme": theme if theme in ("light", "dark") else "light"}
