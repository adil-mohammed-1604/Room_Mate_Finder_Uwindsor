# Owner: Nazim Ali Firdous
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from .forms import (
    LifestyleForm,
    LoginForm,
    PasswordResetRequestForm,
    ProfileForm,
    SetNewPasswordForm,
    SignUpForm,
    VerificationUploadForm,
)
from .models import LifestylePreference, User, VerificationDocument


# ---------------------------------------------------------------------------
# Our own authentication views: sign up, login, logout, forgot password
# ---------------------------------------------------------------------------

def _safe_next(request, default):
    """Where to go after login: the ?next= page if it is on this site, otherwise `default`."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return default


@sensitive_post_parameters("password1", "password2")
@csrf_protect
@never_cache
def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        # Start the session straight away (the backend path tells Django how to reload the user)
        login(request, user, backend="accounts.backends.EmailBackend")
        messages.success(request, "Welcome! Create your profile to get started.")
        return redirect("profile_create")
    return render(request, "registration/signup.html", {"form": form})


@sensitive_post_parameters("password")
@csrf_protect
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect(_safe_next(request, settings.LOGIN_REDIRECT_URL))
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)  # new session id + remembers the user
        return redirect(_safe_next(request, settings.LOGIN_REDIRECT_URL))
    next_url = request.POST.get("next") or request.GET.get("next", "")
    return render(request, "registration/login.html", {"form": form, "next": next_url})


@require_POST  # a GET (e.g. a link or image tag) must not log anyone out
def logout_view(request):
    logout(request)  # deletes the session
    return redirect(settings.LOGOUT_REDIRECT_URL)


def _send_reset_email(request, user):
    context = {
        "user": user,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "token": default_token_generator.make_token(user),
        "protocol": request.scheme,
        "domain": request.get_host(),
        "brand_name": settings.SITE_NAME,
        "support_email": settings.SUPPORT_EMAIL,
        "expiry_hours": settings.PASSWORD_RESET_TIMEOUT // 3600,
    }
    subject = render_to_string("registration/password_reset_subject.txt", context)
    subject = "".join(subject.splitlines()).strip()
    body = render_to_string("registration/password_reset_email.html", context)
    html = render_to_string("registration/password_reset_email_html.html", context)
    message = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
    message.attach_alternative(html, "text/html")
    message.send()


@csrf_protect
def password_reset_view(request):
    form = PasswordResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if user is not None:
            _send_reset_email(request, user)
        # Same page either way, so nobody can test which emails have accounts
        return redirect("password_reset_done")
    return render(request, "registration/password_reset_form.html", {"form": form})


def password_reset_done_view(request):
    return render(request, "registration/password_reset_done.html")


@sensitive_post_parameters("new_password1", "new_password2")
@csrf_protect
@never_cache
def password_reset_confirm_view(request, uidb64, token):
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    # The token is tied to the current password hash, so it stops working once used
    validlink = user is not None and default_token_generator.check_token(user, token)

    form = None
    if validlink:
        form = SetNewPasswordForm(user, request.POST or None)
        if request.method == "POST" and form.is_valid():
            form.save()
            return redirect("password_reset_complete")
    return render(
        request, "registration/password_reset_confirm.html", {"form": form, "validlink": validlink}
    )


def password_reset_complete_view(request):
    return render(request, "registration/password_reset_complete.html")


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
            messages.success(request, "Your profile has been created.")
            return redirect("profile_detail", pk=profile.pk)
    else:
        pform = ProfileForm()
        lform = LifestyleForm()

    return render(
        request,
        "accounts/profile_form.html",
        {"pform": pform, "lform": lform, "title": "Create your profile"},
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
            messages.success(request, "Your profile has been updated.")
            return redirect("profile_detail", pk=profile.pk)
    else:
        pform = ProfileForm(instance=profile)
        lform = LifestyleForm(instance=lifestyle)

    return render(
        request,
        "accounts/profile_form.html",
        {"pform": pform, "lform": lform, "title": "Edit your profile"},
    )


@login_required
def profile_delete(request):
    if not hasattr(request.user, "profile"):
        return redirect("home")
    if request.method == "POST":
        request.user.profile.delete()
        messages.success(request, "Your profile has been deleted.")
        return redirect("home")
    return render(request, "accounts/profile_confirm_delete.html")

@login_required
def verify_upload(request):
    if not hasattr(request.user, "profile"):
        messages.info(request, "Create your profile first.")
        return redirect("profile_create")
    profile = request.user.profile
    if profile.is_verified:
        messages.info(request, "You are already a Verified Student.")
        return redirect("profile_detail", pk=profile.pk)

    latest = profile.verification_documents.first()
    pending = latest is not None and latest.status == "pending"

    if request.method == "POST" and not pending:
        form = VerificationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.profile = profile
            doc.save()
            messages.success(request, "Student ID uploaded. An admin will review it soon.")
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