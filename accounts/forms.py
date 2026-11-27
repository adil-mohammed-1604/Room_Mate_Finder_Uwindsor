# Owner: Nazim Ali Firdous
from django import forms

# Owner: Nazim Ali Firdous
import os

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from profiles.models import Profile

from .models import LifestylePreference, User, UserManager, VerificationDocument


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )


# ---------------------------------------------------------------------------
# Our own authentication forms (plain forms.Form, no Django auth forms)
# ---------------------------------------------------------------------------

class PasswordPairMixin:
    """Checks that two password boxes match and that the password is strong enough."""

    pair = ("password1", "password2")

    def clean(self):
        cleaned = super().clean()
        first, second = (cleaned.get(name) for name in self.pair)
        if first and second and first != second:
            self.add_error(self.pair[1], "The two passwords do not match.")
        elif first:
            try:
                # The rules from AUTH_PASSWORD_VALIDATORS in settings.py
                validate_password(first, user=self.password_user())
            except forms.ValidationError as error:
                self.add_error(self.pair[0], error)
        return cleaned

    def password_user(self):
        return None


class SignUpForm(PasswordPairMixin, forms.Form):
    """Sign up with an email and a password (typed twice)."""

    email = forms.EmailField(label="Email", max_length=254)
    password1 = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", strip=False, widget=forms.PasswordInput)

    def clean_email(self):
        email = UserManager.clean_email(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def password_user(self):
        # Lets the "too similar to your email" rule compare against the new email
        return User(email=self.cleaned_data.get("email", ""))

    def save(self):
        return User.objects.create_user(
            email=self.cleaned_data["email"], password=self.cleaned_data["password1"]
        )


class LoginForm(forms.Form):
    """Log in with email + password. The actual check is in accounts/backends.py."""

    email = forms.CharField(label="Email", max_length=254)  # CharField: bad input gets the same error
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)

    error_message = "Please enter a correct email and password. Both fields may be case-sensitive."

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = UserManager.clean_email(self.cleaned_data.get("email"))
        password = self.cleaned_data.get("password")
        if email and password:
            self.user = authenticate(self.request, email=email, password=password)
            if self.user is None:
                raise forms.ValidationError(self.error_message, code="invalid_login")
        return self.cleaned_data


class PasswordResetRequestForm(forms.Form):
    """Forgot-password form: asks for the email address."""

    email = forms.EmailField(label="Email", max_length=254)

    def get_user(self):
        email = UserManager.clean_email(self.cleaned_data["email"])
        return User.objects.filter(email__iexact=email, is_active=True).first()


class SetNewPasswordForm(PasswordPairMixin, forms.Form):
    """Choose a new password (opened from the reset email link)."""

    pair = ("new_password1", "new_password2")
    new_password1 = forms.CharField(label="New password", strip=False, widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm password", strip=False, widget=forms.PasswordInput)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def password_user(self):
        return self.user

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save(update_fields=["password"])
        return self.user


class ProfileForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "program", "bio", "phone", "budget", "preferred_area", "photo"]
        labels = {
            "full_name": "Full name", "program": "Program", "bio": "Bio",
            "phone": "Phone", "budget": "Budget", "preferred_area": "Preferred area",
            "photo": "Photo",
        }
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}

    def clean_budget(self):
        budget = self.cleaned_data["budget"]
        if budget <= 0:
            raise forms.ValidationError("Budget must be greater than 0.")
        return budget

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if photo and hasattr(photo, "size"):
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Photo too large (max 2 MB).")
            ext = os.path.splitext(photo.name)[1].lower()
            if ext not in (".jpg", ".jpeg", ".png"):
                raise forms.ValidationError("Photo must be a JPG or PNG.")
        return photo


class LifestyleForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = LifestylePreference
        fields = ["sleep_schedule", "cleanliness", "pets", "smoking", "guests_often"]
        labels = {
            "sleep_schedule": "Sleep schedule", "cleanliness": "Cleanliness",
            "pets": "Pets", "smoking": "Smoking", "guests_often": "Guests often",
        }
        widgets = {"cleanliness": forms.NumberInput(attrs={"min": 1, "max": 5})}

class VerificationUploadForm(forms.ModelForm):
    class Meta:
        model = VerificationDocument
        fields = ["student_id"]
        labels = {"student_id": "Student ID file"}
        widgets = {"student_id": forms.ClearableFileInput(attrs={"class": "form-control"})}
