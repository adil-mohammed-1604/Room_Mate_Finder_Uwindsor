# Owner: Alyan Khowaja

import csv
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from profiles.models import Profile
from roommate_finder.csv_utils import safe_cell

from .forms import ContactForm, RoommateRequestForm
from .models import RoommateRequest, VisitLog
from .notifications import notify_new_request, notify_response
@login_required
def send_request(request, profile_id):
    target = get_object_or_404(Profile, pk=profile_id)

    if target.user_id == request.user.id:
        messages.error(request, _("You can't send a request to yourself."))
        return redirect("profile_detail", pk=target.pk)

    if not hasattr(request.user, "profile"):
        messages.info(request, _("Create your profile before sending requests."))
        return redirect("profile_create")

    if RoommateRequest.objects.filter(
        sender=request.user, receiver=target.user, status__in=["pending", "accepted"]
    ).exists():
        messages.info(request, _("You already have an active request with this student."))
        return redirect("profile_detail", pk=target.pk)

    if request.method == "POST":
        form = RoommateRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.sender = request.user
            req.receiver = target.user
            req.save()
            notify_new_request(req, request.build_absolute_uri(reverse("request_inbox")))
            messages.success(request, _("Roommate request sent."))
            return redirect("request_inbox")
    else:
        form = RoommateRequestForm()

    return render(request, "matches/send_request.html", {"form": form, "target": target})


@login_required
def request_inbox(request):
    sent = RoommateRequest.objects.filter(sender=request.user).select_related("receiver__profile")
    received = RoommateRequest.objects.filter(receiver=request.user).select_related(
        "sender__profile"
    )
    return render(request, "matches/request_inbox.html", {"sent": sent, "received": received})


def _respond(request, pk, new_status, **lookup):
    req = get_object_or_404(RoommateRequest, pk=pk, status="pending", **lookup)
    req.status = new_status
    req.responded_at = timezone.now()
    req.save()
    if new_status in ("accepted", "declined"):
        notify_response(req, request.build_absolute_uri(reverse("request_inbox")))
    messages.success(request, _("Request %(status)s.") % {"status": req.get_status_display().lower()})
    return redirect("request_inbox")


@login_required
@require_POST
def accept_request(request, pk):
    return _respond(request, pk, "accepted", receiver=request.user)


@login_required
@require_POST
def decline_request(request, pk):
    return _respond(request, pk, "declined", receiver=request.user)


@login_required
@require_POST
def withdraw_request(request, pk):
    return _respond(request, pk, "withdrawn", sender=request.user)

def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Thanks! Your message has been sent."))
            return redirect("contact")
    else:
        initial = {}
        if request.user.is_authenticated:
            profile = getattr(request.user, "profile", None)
            initial = {
                "name": profile.full_name if profile else "",
                "email": request.user.email,
            }
        form = ContactForm(initial=initial)
    return render(request, "contact.html", {"form": form})


@login_required
def history(request):
    visits_per_day = (
        VisitLog.objects.filter(user=request.user)
        .annotate(day=TruncDate("visited_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("-day")[:7]
    )

    # Last visit comes from the cookie value saved at the start of this session
    last_visit = None
    previous = request.session.get("previous_visit", "")
    if previous.isdigit():
        last_visit = datetime.fromtimestamp(int(previous), tz=timezone.get_current_timezone())

    # Recently viewed profiles come from the session, newest first
    ids = request.session.get("recent_profiles", [])
    by_id = {p.pk: p for p in Profile.objects.filter(pk__in=ids)}
    recent = [by_id[i] for i in ids if i in by_id]

    return render(
        request,
        "matches/history.html",
        {"visits_per_day": visits_per_day, "last_visit": last_visit, "recent": recent},
    )


@login_required
def history_export(request):
    """Download every page view recorded for the logged-in user as a CSV file."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="my_history.csv"'
    writer = csv.writer(response)
    writer.writerow([_("Visited at"), _("Page")])
    visits = VisitLog.objects.filter(user=request.user).order_by("-visited_at")[:5000]
    for visit in visits:
        writer.writerow([timezone.localtime(visit.visited_at).strftime("%Y-%m-%d %H:%M:%S"),
                         safe_cell(visit.path)])
    return response
