# Owner: Mohammed Adil
from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("profile/<int:pk>/", views.ProfileDetailView.as_view(), name="profile_detail"),
    path("saved/", views.saved_list, name="saved_list"),
    path("saved/export.csv", views.saved_export, name="saved_export"),
    path("compare/", views.compare_profiles, name="compare_profiles"),
    path("saved/add/<int:pk>/", views.save_profile, name="save_profile"),
    path("saved/remove/<int:pk>/", views.unsave_profile, name="unsave_profile"),
]