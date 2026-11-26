# Owner: Alyan Khowaja
import time

SKIP_PREFIXES = ("/admin/", "/manage/", "/i18n/", "/static/", "/media/", "/favicon")


class VisitTrackingMiddleware:
    """Logs page views, sets the last_visit cookie, and remembers recently viewed profiles."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(SKIP_PREFIXES):
            return self.get_response(request)

        if not request.session.session_key:
            request.session.create()

        # A new browser session counts as a new visit
        new_visit = not request.session.get("visit_started")
        if new_visit:
            request.session["previous_visit"] = request.COOKIES.get("last_visit", "")
            request.session["visit_started"] = True

        response = self.get_response(request)

        if new_visit:
            response.set_cookie(
                "last_visit", str(int(time.time())), max_age=60 * 60 * 24 * 365, samesite="Lax"
            )

        if request.method == "GET" and response.status_code == 200:
            from .models import VisitLog

            VisitLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key or "",
                path=request.path[:255],
            )
            match = request.resolver_match
            if match and match.url_name == "profile_detail":
                pk = match.kwargs.get("pk")
                recent = [i for i in request.session.get("recent_profiles", []) if i != pk]
                request.session["recent_profiles"] = ([pk] + recent)[:5]

        return response