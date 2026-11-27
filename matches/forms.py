# Owner: Alyan Khowaja
from django import forms

from .models import ContactMessage, RoommateRequest


class RoommateRequestForm(forms.ModelForm):
    class Meta:
        model = RoommateRequest
        fields = ["message"]
        labels = {"message": "Message"}
        widgets = {
            "message": forms.Textarea(
                attrs={"rows": 4, "class": "form-control",
                       "placeholder": "Introduce yourself (optional)"}
            )
        }
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        labels = {"name": "Name", "email": "Email", "subject": "Subject", "message": "Message"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write at least 10 characters.")
        return message