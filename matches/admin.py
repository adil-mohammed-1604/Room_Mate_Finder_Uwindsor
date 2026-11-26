from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import ContactMessage, RoommateRequest, VisitLog


@admin.register(RoommateRequest)
class RoommateRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at", "responded_at")
    list_filter = ("status",)


@admin.register(VisitLog)
class VisitLogAdmin(admin.ModelAdmin):
    list_display = ("user", "session_key", "path", "visited_at")
    list_filter = ("visited_at",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "created_at", "is_resolved")
    list_filter = ("is_resolved",)