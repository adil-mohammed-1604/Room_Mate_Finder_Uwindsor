from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import LifestylePreference, User, VerificationDocument


@admin.register(LifestylePreference)
class LifestylePreferenceAdmin(admin.ModelAdmin):
    list_display = ("profile", "sleep_schedule", "cleanliness", "pets", "smoking")


def _sync_verified(profile):
    profile.is_verified = profile.verification_documents.filter(status="approved").exists()
    profile.save(update_fields=["is_verified"])


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ("profile", "status", "uploaded_at", "reviewed_at")
    list_filter = ("status",)
    fields = ("profile", "document_link", "status", "admin_notes", "uploaded_at", "reviewed_at")
    readonly_fields = ("document_link", "uploaded_at", "reviewed_at")
    actions = ["approve_documents", "reject_documents"]

    @admin.display(description="Student ID")
    def document_link(self, obj):
        if not obj or not obj.pk:
            return "-"
        url = reverse("private_document", args=[obj.pk])
        return format_html('<a href="{}" target="_blank">View student ID</a>', url)

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
        _sync_verified(obj.profile)

    def _set_status(self, queryset, status):
        for doc in queryset:
            doc.status = status
            doc.reviewed_at = timezone.now()
            doc.save()
            _sync_verified(doc.profile)

    @admin.action(description="Approve selected (gives Verified badge)")
    def approve_documents(self, request, queryset):
        self._set_status(queryset, "approved")

    @admin.action(description="Reject selected")
    def reject_documents(self, request, queryset):
        self._set_status(queryset, "rejected")


class EmailUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)


class EmailUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin screen for users: everything is based on the email address."""

    form = EmailUserChangeForm
    add_form = EmailUserCreationForm
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
