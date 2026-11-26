# Owner: Alyan Khowaja

import csv
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
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
from .models import FAQItem, InfoPage, RoommateRequest, TeamMember, VisitLog
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

    # One query covers both directions: my request to them, or their open request to me
    open_requests = RoommateRequest.objects.filter(
        sender__in=[request.user, target.user], receiver__in=[request.user, target.user],
        status__in=["pending", "accepted"],
    ).only("sender_id", "status")
    for existing in open_requests:
        if existing.sender_id == request.user.id:
            messages.info(request, _("You already have an active request with this student."))
            return redirect("profile_detail", pk=target.pk)
        if existing.status == "pending":
            messages.info(request, _("This student already sent you a request. Reply to it here."))
            return redirect("request_inbox")

    if request.method == "POST":
        form = RoommateRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.sender = request.user
            req.receiver = target.user
            try:
                with transaction.atomic():
                    req.save()
            except IntegrityError:  # a double click or second tab got there first
                messages.info(request, _("You already have an active request with this student."))
                return redirect("profile_detail", pk=target.pk)
            notify_new_request(req, request.build_absolute_uri(reverse("request_inbox")))
            messages.success(request, _("Roommate request sent."))
            return redirect("request_inbox")
    else:
        form = RoommateRequestForm()

    return render(request, "matches/send_request.html", {"form": form, "target": target})


REQUEST_STATUSES = ("pending", "accepted", "declined", "withdrawn")


def _filtered(queryset, status):
    return queryset.filter(status=status) if status in REQUEST_STATUSES else queryset


@login_required
def request_inbox(request):
    """Received and sent requests. ?status=pending|accepted|declined|withdrawn filters both lists,
    ?page_received= and ?page_sent= page through them (settings.REQUESTS_PAGE_SIZE per page)."""
    status = request.GET.get("status", "")
    size = getattr(settings, "REQUESTS_PAGE_SIZE", 10)

    base = RoommateRequest.objects.select_related("sender__profile", "receiver__profile")
    received = _filtered(base.filter(receiver=request.user), status)
    sent = _filtered(base.filter(sender=request.user), status)

    return render(request, "matches/request_inbox.html", {
        "received_page": Paginator(received, size).get_page(request.GET.get("page_received")),
        "sent_page": Paginator(sent, size).get_page(request.GET.get("page_sent")),
        "status": status if status in REQUEST_STATUSES else "",
        "statuses": [(value, label) for value, label in RoommateRequest.STATUS],
    })


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

def about(request):
    page = InfoPage.objects.filter(slug="about").first()
    return render(request, "about.html", {"page": page})


def team(request):
    return render(request, "team.html", {"members": TeamMember.objects.filter(is_active=True)})


def faq(request):
    return render(request, "faq.html", {"items": FAQItem.objects.filter(is_published=True)})


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


def _history_days(request):
    """How many days of page views to show: ?days=, else the person's last choice, else the default."""
    choices = getattr(settings, "HISTORY_DAY_CHOICES", (7, 14, 30, 90))
    default = getattr(settings, "HISTORY_DEFAULT_DAYS", 7)
    for value in (request.GET.get("days"), request.session.get("history_days")):
        if value and str(value).isdigit() and int(value) in choices:
            days = int(value)
            if request.GET.get("days") and request.session.get("history_days") != days:
                request.session["history_days"] = days  # remembered for next time
            return days, choices
    return default, choices


@login_required
def history(request):
    days, choices = _history_days(request)
    since = timezone.now() - timedelta(days=days)
    visits_per_day = (
        VisitLog.objects.filter(user=request.user, visited_at__gte=since)
        .annotate(day=TruncDate("visited_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("-day")
    )

    # Last visit comes from the cookie value saved at the start of this session
    last_visit = None
    previous = request.session.get("previous_visit", "")
    if previous.isdigit():
        last_visit = datetime.fromtimestamp(int(previous), tz=timezone.get_current_timezone())

    # Recently viewed profiles come from the session, newest first
    ids = request.session.get("recent_profiles", [])
    by_id = {p.pk: p for p in Profile.objects.filter(pk__in=ids).only("id", "full_name", "program")}
    recent = [by_id[i] for i in ids if i in by_id]

    return render(
        request,
        "matches/history.html",
        {"visits_per_day": visits_per_day, "last_visit": last_visit, "recent": recent,
         "days": days, "day_choices": choices},
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
