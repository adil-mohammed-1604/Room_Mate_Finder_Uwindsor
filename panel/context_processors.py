"""Turns settings.PANEL_THEME into CSS variables for the staff panel and the /admin/ pages."""
from django.conf import settings

DEFAULT_THEME = {
    "brand_name": "RoomMate Admin",
    "primary": "#1E3A5F",      # sidebar, headings, main buttons
    "accent": "#FF6B6B",       # highlights and active menu item
    "background": "#F4F7FB",   # page background
    "surface": "#FFFFFF",      # cards and tables
    "text": "#1F2933",
    "success": "#2EAD6B",
    "danger": "#D64545",
    "radius": "12px",          # corner roundness of cards and buttons
    "dark_background": "#0f1722",  # dark mode: page, cards, sidebar and text
    "dark_surface": "#18222f",
    "dark_sidebar": "#0a111b",
    "dark_text": "#e5ecf4",
    "font": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
}


def panel_theme(request):
    theme = {**DEFAULT_THEME, **getattr(settings, "PANEL_THEME", {})}
    css_vars = "".join(f"--panel-{key.replace('_', '-')}:{value};" for key, value in theme.items()
                       if key != "brand_name")
    return {"PANEL_THEME": theme, "PANEL_CSS_VARS": css_vars}
