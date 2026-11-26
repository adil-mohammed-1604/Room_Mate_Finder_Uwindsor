# Owner: Alyan Khowaja
import time

from django.conf import settings
from django.core.cache import cache

DEFAULTS = {
    "ENABLED": True,
    "SKIP_PREFIXES": ("/admin/", "/manage/", "/i18n/", "/static/", "/media/", "/favicon"),
    "DEDUPE_SECONDS": 5,
    "RECENT_PROFILES": 5,
}


def tracking_config():
    return {**DEFAULTS, **getattr(settings, "VISIT_TRACKING", {})}


class VisitTrackingMiddleware:
    """Logs page views, sets the last_visit cookie, and remembers recently viewed profiles.

    Everything is controlled by settings.VISIT_TRACKING. To keep requests cheap it
      * does nothing for static/admin URLs or when tracking is switched off,
      * only writes a row for successful HTML page loads (not downloads or AJAX calls),
      * skips a repeat of the same page within DEDUPE_SECONDS (double clicks and refreshes), and
      * never writes to the session on an ordinary page view (the repeat check uses the cache).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        config = tracking_config()
        if not config["ENABLED"] or request.path.startswith(tuple(config["SKIP_PREFIXES"])):
            return self.get_response(request)

        session = request.session
        if not session.session_key:
            session.create()

        # A new browser session counts as a new visit
        new_visit = not session.get("visit_started")
        if new_visit:
            session["previous_visit"] = request.COOKIES.get("last_visit", "")
            session["visit_started"] = True

        response = self.get_response(request)

        if new_visit:
            response.set_cookie(
                "last_visit", str(int(time.time())), max_age=60 * 60 * 24 * 365, samesite="Lax"
            )

        if self._is_page_view(request, response):
            self._record(request, config)
        return response

    @staticmethod
    def _is_page_view(request, response):
        return (
            request.method == "GET"
            and response.status_code == 200
            and request.headers.get("x-requested-with") != "XMLHttpRequest"
            and response.get("Content-Type", "").startswith("text/html")
        )

    @staticmethod
    def _record(request, config):
        from .models import VisitLog

        session = request.session
        path = request.path[:255]

        # cache.add() only succeeds the first time, so a repeat within DEDUPE_SECONDS costs no database work
        window = config["DEDUPE_SECONDS"]
        repeated = bool(window) and not cache.add(f"visit:{session.session_key}:{path}", 1, window)
        if not repeated:
            VisitLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=session.session_key or "",
                path=path,
            )

        match = request.resolver_match
        if match and match.url_name == "profile_detail":
            pk = match.kwargs.get("pk")
            recent = session.get("recent_profiles", [])
            if not recent or recent[0] != pk:
                recent = [i for i in recent if i != pk]
                session["recent_profiles"] = ([pk] + recent)[: config["RECENT_PROFILES"]]
