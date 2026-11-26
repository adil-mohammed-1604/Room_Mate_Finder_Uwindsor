# Owner: Nazim Ali Firdous
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.generic import CreateView

from .forms import LifestyleForm, ProfileForm, SignUpForm, VerificationUploadForm
from .models import LifestylePreference, VerificationDocument

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, _("Welcome! Create your profile to get started."))
        return redirect("profile_create")


@login_required
def profile_create(request):
    if hasattr(request.user, "profile"):
        return redirect("profile_edit")

    if request.method == "POST":
        pform = ProfileForm(request.POST, request.FILES)
        lform = LifestyleForm(request.POST)
        if pform.is_valid() and lform.is_valid():
            profile = pform.save(commit=False)
            profile.user = request.user
            profile.save()
            lifestyle = lform.save(commit=False)
            lifestyle.profile = profile
            lifestyle.save()
            messages.success(request, _("Your profile has been created."))
            return redirect("profile_detail", pk=profile.pk)
    else:
        pform = ProfileForm()
        lform = LifestyleForm()

    return render(
        request,
        "accounts/profile_form.html",
        {"pform": pform, "lform": lform, "title": _("Create your profile")},
    )


@login_required
def profile_edit(request):
    if not hasattr(request.user, "profile"):
        return redirect("profile_create")
    profile = request.user.profile
    lifestyle = LifestylePreference.objects.filter(profile=profile).first()

    if request.method == "POST":
        pform = ProfileForm(request.POST, request.FILES, instance=profile)
        lform = LifestyleForm(request.POST, instance=lifestyle)
        if pform.is_valid() and lform.is_valid():
            pform.save()
            lifestyle = lform.save(commit=False)
            lifestyle.profile = profile
            lifestyle.save()
            messages.success(request, _("Your profile has been updated."))
            return redirect("profile_detail", pk=profile.pk)
    else:
        pform = ProfileForm(instance=profile)
        lform = LifestyleForm(instance=lifestyle)

    return render(
        request,
        "accounts/profile_form.html",
        {"pform": pform, "lform": lform, "title": _("Edit your profile")},
    )


@login_required
def profile_delete(request):
    if not hasattr(request.user, "profile"):
        return redirect("home")
    if request.method == "POST":
        request.user.profile.delete()
        messages.success(request, _("Your profile has been deleted."))
        return redirect("home")
    return render(request, "accounts/profile_confirm_delete.html")

@login_required
def verify_upload(request):
    if not hasattr(request.user, "profile"):
        messages.info(request, _("Create your profile first."))
        return redirect("profile_create")
    profile = request.user.profile
    if profile.is_verified:
        messages.info(request, _("You are already a Verified Student."))
        return redirect("profile_detail", pk=profile.pk)

    latest = profile.verification_documents.first()
    pending = latest is not None and latest.status == "pending"

    if request.method == "POST" and not pending:
        form = VerificationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.profile = profile
            doc.save()
            messages.success(request, _("Student ID uploaded. An admin will review it soon."))
            return redirect("profile_detail", pk=profile.pk)
    else:
        form = VerificationUploadForm()

    return render(
        request, "accounts/verify_upload.html", {"form": form, "latest": latest, "pending": pending}
    )


@staff_member_required
def private_document(request, pk):
    # Only staff can open a student ID
    doc = get_object_or_404(VerificationDocument, pk=pk)
    return FileResponse(doc.student_id.open("rb"))