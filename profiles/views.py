# Owner: Mohammed Adil
import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from accounts.models import LifestylePreference
from matches.models import RoommateRequest

from roommate_finder.csv_utils import safe_cell

from .completeness import profile_completeness
from .matching import compatibility_score, score_breakdown
from .models import Area, Profile, SavedProfile

# Inclusive (min, max) monthly budget ranges
BUDGET_RANGES = {
    "under_600": (0, 599),
    "600_900": (600, 900),
    "900_1200": (901, 1200),
    "over_1200": (1201, None),
}
BUDGET_CHOICES = [
    ("under_600", gettext_lazy("Under $600")),
    ("600_900", "$600 - $900"),
    ("900_1200", "$900 - $1,200"),
    ("over_1200", gettext_lazy("Over $1,200")),
]
GUEST_LIMIT = 6
SORT_CHOICES = [
    ("match", gettext_lazy("Best match")),
    ("budget_low", gettext_lazy("Budget: low to high")),
    ("budget_high", gettext_lazy("Budget: high to low")),
    ("newest", gettext_lazy("Newest first")),
]
SORT_ORDER = {
    "match": ("-is_verified", "-created_at"),
    "budget_low": ("budget", "-is_verified"),
    "budget_high": ("-budget", "-is_verified"),
    "newest": ("-created_at",),
}


def _my_profile(user):
    # Safe lookup: returns None for guests or users without a profile
    return getattr(user, "profile", None) if user.is_authenticated else None


class HomeView(ListView):
    model = Profile
    template_name = "home.html"
    context_object_name = "profiles"

    def get_paginate_by(self, queryset):
        return 9 if self.request.user.is_authenticated else None

    def get_queryset(self):
        user = self.request.user
        get = self.request.GET
        qs = Profile.objects.select_related("user", "preferred_area", "lifestyle")

        if user.is_authenticated:
            qs = qs.exclude(user=user)

        q = get.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(full_name__icontains=q) | Q(program__icontains=q) | Q(bio__icontains=q)
            )

        # Invalid filter values are ignored instead of causing errors
        budget = get.get("budget", "")
        if budget in BUDGET_RANGES:
            low, high = BUDGET_RANGES[budget]
            qs = qs.filter(budget__gte=low)
            if high is not None:
                qs = qs.filter(budget__lte=high)

        lifestyle = get.get("lifestyle", "")
        if lifestyle in dict(LifestylePreference.SLEEP):
            qs = qs.filter(lifestyle__sleep_schedule=lifestyle)

        area = get.get("area", "")
        if area.isdigit() and len(area) <= 9:
            qs = qs.filter(preferred_area_id=int(area))

        sort = get.get("sort", "")
        if sort not in SORT_ORDER:
            sort = "match"
        qs = qs.order_by(*SORT_ORDER[sort])

        if not user.is_authenticated:
            return qs[:GUEST_LIMIT]

        # Logged in: attach a score to each profile and rank by it
        profiles = list(qs)
        mine = _my_profile(user)
        for p in profiles:
            p.score = compatibility_score(mine, p) if mine else None
        if mine and sort == "match":
            profiles.sort(key=lambda p: (-p.score, not p.is_verified))
        return profiles

    def _completeness(self):
        mine = _my_profile(self.request.user)
        return profile_completeness(mine) if mine else None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx.update(
            {
                "areas": Area.objects.all(),
                "budget_choices": BUDGET_CHOICES,
                "lifestyle_choices": LifestylePreference.SLEEP,
                "q": self.request.GET.get("q", ""),
                "sel_budget": self.request.GET.get("budget", ""),
                "sel_lifestyle": self.request.GET.get("lifestyle", ""),
                "sel_area": self.request.GET.get("area", ""),
                "sort_choices": SORT_CHOICES,
                "sel_sort": self.request.GET.get("sort", ""),
                "querystring": params.urlencode(),
                "has_profile": _my_profile(self.request.user) is not None,
                "completeness": self._completeness(),
            }
        )
        return ctx


class ProfileDetailView(DetailView):
    model = Profile
    template_name = "profiles/profile_detail.html"
    context_object_name = "profile"

    def get_queryset(self):
        return Profile.objects.select_related("user", "preferred_area", "lifestyle")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        me = self.request.user
        other = self.object.user
        existing = None
        can_see_contact = False
        score = None
        breakdown = None
        is_saved = False
        if me.is_authenticated and me != other:
            existing = RoommateRequest.objects.filter(
                Q(sender=me, receiver=other) | Q(sender=other, receiver=me),
                status__in=["pending", "accepted"],
            ).first()
            can_see_contact = bool(existing and existing.status == "accepted")
            mine = _my_profile(me)
            if mine:
                breakdown = score_breakdown(mine, self.object)
                score = breakdown["score"]
            is_saved = SavedProfile.objects.filter(user=me, profile=self.object).exists()
        is_own = me.is_authenticated and me == other
        ctx.update(
            {
                "breakdown": breakdown,
                "completeness": profile_completeness(self.object) if is_own else None,
                "existing_request": existing,
                "can_see_contact": can_see_contact,
                "is_own_profile": me.is_authenticated and me == other,
                "score": score,
                "is_saved": is_saved,
            }
        )
        return ctx


def _back(request, fallback_pk):
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect("profile_detail", pk=fallback_pk)


@login_required
@require_POST
def save_profile(request, pk):
    profile = get_object_or_404(Profile, pk=pk)
    if profile.user_id == request.user.id:
        messages.error(request, _("You can't save your own profile."))
    else:
        _saved, created = SavedProfile.objects.get_or_create(user=request.user, profile=profile)
        messages.success(
            request, _("Added to your shortlist.") if created else _("Already in your shortlist.")
        )
    return _back(request, pk)


@login_required
@require_POST
def unsave_profile(request, pk):
    SavedProfile.objects.filter(user=request.user, profile_id=pk).delete()
    messages.success(request, _("Removed from your shortlist."))
    return _back(request, pk)


@login_required
def saved_list(request):
    saved = SavedProfile.objects.filter(user=request.user).select_related(
        "profile__user", "profile__preferred_area", "profile__lifestyle"
    )
    mine = _my_profile(request.user)
    for s in saved:
        s.score = compatibility_score(mine, s.profile) if mine else None
    return render(request, "profiles/saved_list.html", {"saved": saved})


def _csv_response(filename):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def saved_export(request):
    """Download the shortlist as a CSV file (no contact details are included)."""
    saved = SavedProfile.objects.filter(user=request.user).select_related(
        "profile__preferred_area", "profile__lifestyle"
    )
    mine = _my_profile(request.user)
    response = _csv_response("shortlist.csv")
    writer = csv.writer(response)
    writer.writerow([_("Name"), _("Program"), _("Budget (CAD/month)"), _("Area"), _("Verified"), _("Match %"), _("Saved on")])
    for s in saved:
        p = s.profile
        writer.writerow([
            safe_cell(p.full_name), safe_cell(p.program), p.budget,
            safe_cell(p.preferred_area or ""), _("Yes") if p.is_verified else _("No"),
            compatibility_score(mine, p) if mine else "", s.saved_at.strftime("%Y-%m-%d"),
        ])
    return response


@login_required
def compare_profiles(request):
    """Side-by-side table of exactly two profiles, chosen with ?ids=1&ids=2."""
    ids = []
    for raw in request.GET.getlist("ids"):
        if raw.isdigit() and len(raw) <= 9 and int(raw) not in ids:
            ids.append(int(raw))
    if len(ids) != 2:
        messages.info(request, _("Pick exactly two profiles from your shortlist to compare."))
        return redirect("saved_list")

    found = {
        p.pk: p
        for p in Profile.objects.select_related("user", "preferred_area", "lifestyle").filter(pk__in=ids)
    }
    if len(found) != 2:
        raise Http404("Profile not found")
    profiles = [found[i] for i in ids]
    mine = _my_profile(request.user)

    def life(p, method):
        lifestyle = getattr(p, "lifestyle", None)
        return getattr(lifestyle, method)() if lifestyle else "—"

    def row(label, getter):
        values = [getter(p) for p in profiles]
        return {"label": label, "values": values, "same": values[0] == values[1]}

    rows = [
        row(_("Match with you"), lambda p: f"{compatibility_score(mine, p)}%" if mine and p.pk != mine.pk else "—"),
        row(_("Verified"), lambda p: _("Yes") if p.is_verified else _("No")),
        row(_("Program"), lambda p: p.program or "—"),
        row(_("Budget"), lambda p: _("$%(amount)s/month") % {"amount": p.budget}),
        row(_("Preferred area"), lambda p: str(p.preferred_area) if p.preferred_area else _("Any")),
        row(_("Sleep schedule"), lambda p: life(p, "get_sleep_schedule_display")),
        row(_("Cleanliness"), lambda p: f"{p.lifestyle.cleanliness}/5" if getattr(p, "lifestyle", None) else "—"),
        row(_("Pets"), lambda p: life(p, "get_pets_display")),
        row(_("Smoking"), lambda p: life(p, "get_smoking_display")),
        row(_("Guests often"), lambda p: life(p, "get_guests_often_display")),
    ]
    return render(request, "profiles/compare.html", {"profiles": profiles, "rows": rows})
