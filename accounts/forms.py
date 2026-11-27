# Owner: Nazim Ali Firdous
from django import forms

# Owner: Nazim Ali Firdous
import os
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from profiles.models import Profile

from .models import LifestylePreference, VerificationDocument

User = get_user_model()


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )


class SignUpForm(BootstrapMixin, UserCreationForm):
    """Sign up with an email and a password."""

    email = forms.EmailField(
        required=True, label=_("Email"),
        widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("An account with this email already exists."))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ProfileForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "program", "bio", "phone", "budget", "preferred_area", "photo"]
        labels = {
            "full_name": _("Full name"), "program": _("Program"), "bio": _("Bio"),
            "phone": _("Phone"), "budget": _("Budget"), "preferred_area": _("Preferred area"),
            "photo": _("Photo"),
        }
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}

    def clean_budget(self):
        budget = self.cleaned_data["budget"]
        if budget <= 0:
            raise forms.ValidationError(_("Budget must be greater than 0."))
        return budget

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and hasattr(photo, "size"):
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError(_("Photo too large (max 2 MB)."))
            ext = os.path.splitext(photo.name)[1].lower()
            if ext not in (".jpg", ".jpeg", ".png"):
                raise forms.ValidationError(_("Photo must be a JPG or PNG."))
        return photo


class LifestyleForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = LifestylePreference
        fields = ["sleep_schedule", "cleanliness", "pets", "smoking", "guests_often"]
        labels = {
            "sleep_schedule": _("Sleep schedule"), "cleanliness": _("Cleanliness"),
            "pets": _("Pets"), "smoking": _("Smoking"), "guests_often": _("Guests often"),
        }
        widgets = {"cleanliness": forms.NumberInput(attrs={"min": 1, "max": 5})}

class VerificationUploadForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ["student_id"]
        labels = {"student_id": _("Student ID file")}
        widgets = {"student_id": forms.ClearableFileInput(attrs={"class": "form-control"})}


class StyledAuthenticationForm(BootstrapMixin, AuthenticationForm):
    """Login form: students sign in with their email address."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": _("Please enter a correct email and password. Both fields may be case-sensitive."),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["username"]  # Django always calls this form field "username"; it holds the email
        field.label = _("Email")
        field.widget = forms.EmailInput(
            attrs={"class": "form-control", "autocomplete": "email", "autofocus": True}
        )


class StyledPasswordResetForm(BootstrapMixin, PasswordResetForm):
    """Forgot-password form (asks for the email address)."""


class StyledSetPasswordForm(BootstrapMixin, SetPasswordForm):
    """Choose-a-new-password form shown from the reset email link."""
