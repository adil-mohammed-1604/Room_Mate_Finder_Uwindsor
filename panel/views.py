from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, models, transaction
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, ngettext
from django.views.decorators.http import require_POST

from accounts.admin import _sync_verified
from accounts.models import User, VerificationDocument
from matches.models import ContactMessage, RoommateRequest, VisitLog
from profiles.models import Profile

from .forms import UserPanelForm, make_form_class
from .registry import CONFIG, SECTIONS

PAGE_SIZE = 15
CHART_DAYS = 14

# Badge colours for the "status" column
BADGE_COLOURS = {
    "pending": "warning", "approved": "success", "accepted": "success",
    "rejected": "danger", "declined": "danger", "withdrawn": "secondary",
}
STATUS_COLOURS = {"pending": "#f59e0b", "accepted": "#2EAD6B", "declined": "#d64545", "withdrawn": "#94a3b8"}

# Bulk actions: name -> (label, icon, button style)
BULK_ACTIONS = {
    "approve": (gettext_lazy("Approve"), "bi-check-lg", "success"),
    "reject": (gettext_lazy("Reject"), "bi-x-lg", "warning"),
    "resolve": (gettext_lazy("Mark resolved"), "bi-check-lg", "success"),
    "reopen": (gettext_lazy("Reopen"), "bi-arrow-counterclockwise", "secondary"),
    "delete": (gettext_lazy("Delete"), "bi-trash", "danger"),
}


# ---------------------------------------------------------------- helpers

def panel_required(view):
    """Staff members and superusers only; everyone else is sent to log in or refused."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
        if not (user.is_staff or user.is_superuser):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def get_config(slug):
    try:
        return CONFIG[slug]
    except KeyError:
        raise Http404("Unknown panel section")


def panel_context(request, slug=None, **extra):
    sections = [
        (heading, [(s, CONFIG[s]) for s in slugs if s in CONFIG]) for heading, slugs in SECTIONS
    ]
    context = {"sections": sections, "current_slug": slug}
    context.update(extra)
    return context


def safe_next(request, fallback):
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(target, {request.get_host()}):
        return target
    return fallback


def field_label(model, name):
    """Column / row heading. Django's own fields come already translated; ours use the catalog."""
    return _(str(model._meta.get_field(name).verbose_name).capitalize())


def filter_options(model, name):
    field = model._meta.get_field(name)
    if isinstance(field, models.BooleanField):
        return [("1", _("Yes")), ("0", _("No"))]
    if field.choices:
        return list(field.choices)
    if field.is_relation:
        return [(str(obj.pk), str(obj)) for obj in field.related_model.objects.all()[:100]]
    return []


def initials(text):
    words = [w for w in "".join(c if c.isalnum() else " " for c in text).split() if w]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    return text[:2].upper() if text else "?"


def cell(obj, name, avatar=False):
    field = obj._meta.get_field(name)
    value = getattr(obj, name)
    if value is None or value == "":
        return {"kind": "empty", "value": "—"}
    if isinstance(field, models.BooleanField):
        return {"kind": "bool", "value": value}
    if field.choices:
        text = getattr(obj, f"get_{name}_display")()
        if name == "status":
            return {"kind": "badge", "value": text, "colour": BADGE_COLOURS.get(value, "secondary")}
        return {"kind": "text", "value": text}
    if isinstance(field, models.DateTimeField):
        return {"kind": "date", "value": value}
    if avatar:
        return {"kind": "avatar", "value": str(value), "initials": initials(str(value))}
    return {"kind": "text", "value": str(value)}


def row_actions(slug, obj):
    """Quick buttons shown at the end of each table row."""
    if slug == "verifications":
        actions = [{"label": _("View ID"), "icon": "bi-eye", "url": reverse("private_document", args=[obj.pk]),
                    "style": "outline-secondary", "blank": True}]
        if obj.status != "approved":
            actions.append({"label": _("Approve"), "icon": "bi-check-lg", "style": "success",
                            "post": reverse("panel:action", args=[slug, obj.pk, "approve"])})
        if obj.status != "rejected":
            actions.append({"label": _("Reject"), "icon": "bi-x-lg", "style": "danger",
                            "post": reverse("panel:action", args=[slug, obj.pk, "reject"])})
        return actions
    if slug == "messages":
        if obj.is_resolved:
            return [{"label": _("Reopen"), "icon": "bi-arrow-counterclockwise", "style": "outline-secondary",
                     "post": reverse("panel:action", args=[slug, obj.pk, "reopen"])}]
        return [{"label": _("Resolve"), "icon": "bi-check-lg", "style": "success",
                 "post": reverse("panel:action", args=[slug, obj.pk, "resolve"])}]
    return []


def check_user_target(request, slug, obj):
    """Staff may not touch superusers."""
    if slug == "users" and obj.is_superuser and not request.user.is_superuser:
        raise PermissionDenied


def line_chart(values, width=600, height=150, pad=10):
    """Points for a simple SVG line chart."""
    peak = max(values) or 1
    step = (width - 2 * pad) / max(len(values) - 1, 1)
    points = [(pad + i * step, height - pad - (v / peak) * (height - 2 * pad)) for i, v in enumerate(values)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"{pad},{height - pad} {line} {points[-1][0]:.1f},{height - pad}"
    return line, area, points


# ---------------------------------------------------------------- dashboard

@panel_required
def dashboard(request):
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    start = (now - timedelta(days=CHART_DAYS - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    days = [(start + timedelta(days=i)).date() for i in range(CHART_DAYS)]

    def stat(label, value, icon, slug, new=None, tone="primary"):
        return {"label": label, "value": value, "icon": icon, "slug": slug, "new": new, "tone": tone}

    stats = [
        stat(_("Users"), User.objects.count(), "bi-people", "users",
             User.objects.filter(date_joined__gte=week_ago).count(), "primary"),
        stat(_("Profiles"), Profile.objects.count(), "bi-person-lines-fill", "profiles",
             Profile.objects.filter(created_at__gte=week_ago).count(), "info"),
        stat(_("Verified"), Profile.objects.filter(is_verified=True).count(), "bi-patch-check", "profiles",
             None, "success"),
        stat(_("Pending IDs"), VerificationDocument.objects.filter(status="pending").count(),
             "bi-hourglass-split", "verifications", None, "warning"),
        stat(_("Open messages"), ContactMessage.objects.filter(is_resolved=False).count(),
             "bi-envelope-open", "messages", None, "danger"),
        stat(_("Requests"), RoommateRequest.objects.count(), "bi-people", "requests",
             RoommateRequest.objects.filter(created_at__gte=week_ago).count(), "accent"),
    ]

    # Page views and sign-ups per day (last 14 days)
    visit_counts = {d: 0 for d in days}
    for visited_at in VisitLog.objects.filter(visited_at__gte=start).values_list("visited_at", flat=True):
        day = timezone.localtime(visited_at).date()
        if day in visit_counts:
            visit_counts[day] += 1
    signup_counts = {d: 0 for d in days}
    for joined in User.objects.filter(date_joined__gte=start).values_list("date_joined", flat=True):
        day = timezone.localtime(joined).date()
        if day in signup_counts:
            signup_counts[day] += 1

    visit_values = [visit_counts[d] for d in days]
    line, area, points = line_chart(visit_values)
    visit_chart = {
        "line": line, "area": area, "total": sum(visit_values),
        "points": [{"x": round(x, 1), "y": round(y, 1), "day": d, "count": c}
                   for (x, y), d, c in zip(points, days, visit_values)],
        "first": days[0], "last": days[-1],
    }
    peak = max(signup_counts.values()) or 1
    signup_chart = [{"day": d, "count": c, "height": max(4, round(c / peak * 100)) if c else 4}
                    for d, c in signup_counts.items()]

    # Request status donut (pure CSS conic-gradient)
    totals = {row["status"]: row["total"]
              for row in RoommateRequest.objects.values("status").annotate(total=Count("id"))}
    grand = sum(totals.values())
    status_rows, stops, running = [], [], 0.0
    for key, label in RoommateRequest.STATUS:
        count = totals.get(key, 0)
        status_rows.append({"label": label, "count": count, "colour": STATUS_COLOURS[key]})
        if grand and count:
            share = count / grand * 100
            stops.append(f"{STATUS_COLOURS[key]} {running:.2f}% {running + share:.2f}%")
            running += share
    donut = f"conic-gradient({', '.join(stops)})" if stops else "conic-gradient(#e2e8f0 0 100%)"

    # Verification funnel
    doc_totals = {row["status"]: row["total"]
                  for row in VerificationDocument.objects.values("status").annotate(total=Count("id"))}
    doc_sum = sum(doc_totals.values()) or 1
    funnel = [{"label": label, "count": doc_totals.get(key, 0),
               "percent": round(doc_totals.get(key, 0) / doc_sum * 100),
               "colour": {"pending": "warning", "approved": "success", "rejected": "danger"}[key]}
              for key, label in VerificationDocument.STATUS]

    # Latest activity from several tables, newest first
    activity = []
    for u in User.objects.order_by("-date_joined")[:6]:
        activity.append({"when": u.date_joined, "icon": "bi-person-plus", "tone": "primary",
                         "text": _("%(who)s joined") % {"who": u.email},
                         "url": reverse("panel:edit", args=["users", u.pk])})
    for r in RoommateRequest.objects.select_related("sender", "receiver").order_by("-created_at")[:6]:
        activity.append({"when": r.created_at, "icon": "bi-send", "tone": "accent",
                         "text": _("%(sender)s sent a request to %(receiver)s") % {
                             "sender": r.sender.email, "receiver": r.receiver.email},
                         "url": reverse("panel:edit", args=["requests", r.pk])})
    for m in ContactMessage.objects.order_by("-created_at")[:6]:
        activity.append({"when": m.created_at, "icon": "bi-envelope", "tone": "danger",
                         "text": _("%(name)s wrote: %(subject)s") % {"name": m.name, "subject": m.subject},
                         "url": reverse("panel:edit", args=["messages", m.pk])})
    for d in VerificationDocument.objects.select_related("profile").order_by("-uploaded_at")[:6]:
        activity.append({"when": d.uploaded_at, "icon": "bi-patch-check", "tone": "warning",
                         "text": _("%(who)s uploaded a student ID") % {"who": str(d.profile)},
                         "url": reverse("panel:edit", args=["verifications", d.pk])})
    activity.sort(key=lambda item: item["when"], reverse=True)

    context = panel_context(
        request, stats=stats, visit_chart=visit_chart, signup_chart=signup_chart,
        status_rows=status_rows, request_total=grand, donut=donut, funnel=funnel,
        activity=activity[:10],
        pending_docs=VerificationDocument.objects.filter(status="pending").select_related("profile")[:5],
        open_messages=ContactMessage.objects.filter(is_resolved=False)[:5],
    )
    return render(request, "panel/dashboard.html", context)


# ---------------------------------------------------------------- list

def tab_options(config, model, params):
    """Quick tabs above the table (for example Pending / Approved / Rejected)."""
    name = config.get("tabs")
    if not name:
        return None
    field = model._meta.get_field(name)
    if "tab_labels" in config:
        options = list(config["tab_labels"])
    elif isinstance(field, models.BooleanField):
        options = [("1", _("Yes")), ("0", _("No"))]
    else:
        options = list(field.choices)

    counts = {}
    for row in model.objects.values(name).annotate(total=Count("pk")):
        key = row[name]
        counts[("1" if key else "0") if isinstance(key, bool) else str(key)] = row["total"]

    current = params.get(name, "")
    base = params.copy()
    base.pop("page", None)
    base.pop(name, None)
    tabs = [{"label": _("All"), "count": sum(counts.values()), "active": current == "",
             "qs": base.urlencode()}]
    for value, label in options:
        with_value = base.copy()
        with_value[name] = value
        tabs.append({"label": label, "count": counts.get(str(value), 0), "active": current == str(value),
                     "qs": with_value.urlencode()})
    return tabs


@panel_required
def model_list(request, slug):
    config = get_config(slug)
    model = config["model"]
    queryset = model.objects.all()

    related = [c for c in config["columns"] if model._meta.get_field(c).is_relation]
    if related:
        queryset = queryset.select_related(*related)

    query = request.GET.get("q", "").strip()
    if query and config["search"]:
        condition = Q()
        for lookup in config["search"]:
            condition |= Q(**{f"{lookup}__icontains": query})
        queryset = queryset.filter(condition)

    tab_field = config.get("tabs")
    filters = []
    for name in config["filters"] + ([tab_field] if tab_field else []):
        field = model._meta.get_field(name)
        selected = request.GET.get(name, "")
        if selected != "":
            if isinstance(field, models.BooleanField):
                queryset = queryset.filter(**{name: selected == "1"})
            else:
                queryset = queryset.filter(**{name: selected})
        if name != tab_field:
            filters.append({"name": name, "label": field_label(model, name), "selected": selected,
                            "options": filter_options(model, name)})

    # Sorting by clicking a column heading: ?o=name or ?o=-name
    raw_sort = request.GET.get("o", "")
    sort_name = raw_sort.lstrip("-")
    if sort_name in config["columns"]:
        queryset = queryset.order_by(raw_sort, "-pk")
    else:
        raw_sort, sort_name = "", ""
        queryset = queryset.order_by(config["order"])

    page = Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))

    rows = [{"obj": obj,
             "cells": [cell(obj, c, avatar=config.get("avatar", False) and i == 0)
                       for i, c in enumerate(config["columns"])],
             "actions": row_actions(slug, obj)} for obj in page]

    sort_base = request.GET.copy()
    sort_base.pop("page", None)
    headers = []
    for column in config["columns"]:
        params = sort_base.copy()
        if sort_name == column and not raw_sort.startswith("-"):
            params["o"] = f"-{column}"
        else:
            params["o"] = column
        direction = ""
        if sort_name == column:
            direction = "desc" if raw_sort.startswith("-") else "asc"
        headers.append({"label": field_label(model, column), "qs": params.urlencode(), "direction": direction})

    params = request.GET.copy()
    params.pop("page", None)
    bulk = [{"name": name, "label": BULK_ACTIONS[name][0], "icon": BULK_ACTIONS[name][1],
             "style": BULK_ACTIONS[name][2]} for name in config.get("bulk", []) + ["delete"]]
    context = panel_context(
        request, slug, config=config, rows=rows, headers=headers, page=page, filters=filters,
        query=query, querystring=params.urlencode(), has_actions=any(r["actions"] for r in rows),
        tabs=tab_options(config, model, request.GET), bulk=bulk,
    )
    return render(request, "panel/list.html", context)


# ---------------------------------------------------------------- create / edit / delete

def form_class_for(slug, config):
    return UserPanelForm if slug == "users" else make_form_class(config)


def readonly_details(obj, config):
    return [(field_label(type(obj), name), cell(obj, name)) for name in config.get("readonly", [])]


def after_save(slug, obj, form, creating):
    if slug == "verifications":
        if "status" in form.changed_data:
            obj.reviewed_at = timezone.now()
            obj.save(update_fields=["reviewed_at"])
        _sync_verified(obj.profile)
    elif slug == "requests" and "status" in form.changed_data:
        obj.responded_at = None if obj.status == "pending" else timezone.now()
        obj.save(update_fields=["responded_at"])


@panel_required
def model_create(request, slug):
    config = get_config(slug)
    if not config["can_create"]:
        raise Http404
    form_class = form_class_for(slug, config)
    form = form_class(request.POST or None, request.FILES or None, acting_user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                obj = form.save()
                after_save(slug, obj, form, True)
        except IntegrityError:
            form.add_error(None, _("That would duplicate an existing record."))
        else:
            messages.success(request, _("Record created."))
            return redirect("panel:list", slug=slug)
    context = panel_context(request, slug, config=config, form=form, creating=True, page_title=config["add"])
    return render(request, "panel/form.html", context)


@panel_required
def model_edit(request, slug, pk):
    config = get_config(slug)
    if not config["can_edit"]:
        raise Http404
    obj = get_object_or_404(config["model"], pk=pk)
    check_user_target(request, slug, obj)
    form_class = form_class_for(slug, config)
    form = form_class(request.POST or None, request.FILES or None, instance=obj, acting_user=request.user)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                obj = form.save()
                after_save(slug, obj, form, False)
        except IntegrityError:
            form.add_error(None, _("That change would duplicate an existing record "
                                   "(for example two active requests between the same people)."))
        else:
            messages.success(request, _("Record saved."))
            return redirect("panel:list", slug=slug)
    extra_links = []
    if slug == "verifications":
        extra_links.append({"label": _("Open student ID"), "url": reverse("private_document", args=[obj.pk]),
                            "icon": "bi-eye"})
    context = panel_context(request, slug, config=config, form=form, obj=obj, creating=False,
                            page_title=config["edit"], details=readonly_details(obj, config),
                            extra_links=extra_links)
    return render(request, "panel/form.html", context)


@panel_required
def model_delete(request, slug, pk):
    config = get_config(slug)
    obj = get_object_or_404(config["model"], pk=pk)
    check_user_target(request, slug, obj)
    if slug == "users" and obj.pk == request.user.pk:
        messages.error(request, _("You cannot delete your own account from the panel."))
        return redirect("panel:list", slug=slug)
    if request.method == "POST":
        profile = obj.profile if slug == "verifications" else None
        obj.delete()
        if profile:
            _sync_verified(profile)
        messages.success(request, _("Record deleted."))
        return redirect("panel:list", slug=slug)
    context = panel_context(request, slug, config=config, obj=obj, page_title=config["delete"])
    return render(request, "panel/confirm_delete.html", context)


# ---------------------------------------------------------------- quick row actions and bulk actions

@panel_required
@require_POST
def row_action(request, slug, pk, action):
    config = get_config(slug)
    obj = get_object_or_404(config["model"], pk=pk)
    fallback = reverse("panel:list", args=[slug])

    if slug == "verifications" and action in ("approve", "reject"):
        obj.status = "approved" if action == "approve" else "rejected"
        obj.reviewed_at = timezone.now()
        obj.save()
        _sync_verified(obj.profile)
        messages.success(request, _("ID %(status)s for %(who)s.") % {
            "status": obj.get_status_display().lower(), "who": obj.profile})
    elif slug == "messages" and action in ("resolve", "reopen"):
        obj.is_resolved = action == "resolve"
        obj.save(update_fields=["is_resolved"])
        messages.success(request, _("Message marked as resolved.") if obj.is_resolved
                         else _("Message reopened."))
    else:
        raise Http404
    return redirect(safe_next(request, fallback))


@panel_required
@require_POST
def bulk_action(request, slug):
    """Apply one action to every ticked row of a table."""
    config = get_config(slug)
    model = config["model"]
    fallback = reverse("panel:list", args=[slug])
    action = request.POST.get("action", "")
    if action not in set(config.get("bulk", [])) | {"delete"}:
        raise Http404
    ids = [int(i) for i in request.POST.getlist("ids") if i.isdigit() and len(i) <= 9][:500]
    if not ids:
        messages.info(request, _("Tick at least one row first."))
        return redirect(safe_next(request, fallback))

    items = list(model.objects.filter(pk__in=ids))
    skipped = 0
    if action == "delete" and slug == "users":
        allowed = [u for u in items if u.pk != request.user.pk
                   and (request.user.is_superuser or not u.is_superuser)]
        skipped = len(items) - len(allowed)
        items = allowed

    profiles = {}
    for obj in items:
        if action in ("approve", "reject"):
            obj.status = "approved" if action == "approve" else "rejected"
            obj.reviewed_at = timezone.now()
            obj.save()
            profiles[obj.profile_id] = obj.profile
        elif action in ("resolve", "reopen"):
            obj.is_resolved = action == "resolve"
            obj.save(update_fields=["is_resolved"])
        elif action == "delete":
            if slug == "verifications":
                profiles[obj.profile_id] = obj.profile
            obj.delete()
    for profile in profiles.values():
        _sync_verified(profile)

    done = len(items)
    messages.success(request, ngettext("%(n)d record updated.", "%(n)d records updated.", done) % {"n": done})
    if skipped:
        messages.warning(request, ngettext("%(n)d record was skipped (protected account).",
                                           "%(n)d records were skipped (protected accounts).", skipped)
                         % {"n": skipped})
    return redirect(safe_next(request, fallback))
