from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from accounts.models import User


class PanelFormMixin:
    """Adds Bootstrap classes to every field and accepts the logged-in staff member."""

    def __init__(self, *args, acting_user=None, **kwargs):
        self.acting_user = acting_user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = "form-select"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()
            if isinstance(field.label, str):
                field.label = _(field.label)  # field names like "Full name" come from our French catalog


class PanelModelForm(PanelFormMixin, forms.ModelForm):
    pass


def make_form_class(config):
    return forms.modelform_factory(config["model"], form=PanelModelForm, fields=config["fields"])


class UserPanelForm(PanelFormMixin, forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, required=False, label=gettext_lazy("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput, required=False, label=gettext_lazy("Confirm password"))

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "is_active", "is_staff", "is_superuser"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.creating = self.instance.pk is None
        if not (self.acting_user and self.acting_user.is_superuser):
            # Only superusers can hand out superuser rights.
            del self.fields["is_superuser"]
        if not self.creating:
            self.fields["password1"].label = _("New password (leave empty to keep the current one)")
        else:
            self.fields["is_active"].initial = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if self.creating and not p1:
            self.add_error("password1", _("Password is required for a new user."))
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", _("The two passwords do not match."))
            elif p1:
                try:
                    validate_password(p1, self.instance)
                except forms.ValidationError as error:
                    self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
