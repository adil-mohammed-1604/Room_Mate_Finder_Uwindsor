from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import Area, Profile, SavedProfile


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "budget", "preferred_area", "is_verified", "created_at")
    list_filter = ("is_verified", "preferred_area")
    search_fields = ("full_name", "user__email", "program")


@admin.register(SavedProfile)
class SavedProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "profile", "saved_at")