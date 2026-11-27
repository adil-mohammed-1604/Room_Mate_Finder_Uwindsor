from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("<slug:slug>/", views.model_list, name="list"),
    path("<slug:slug>/bulk/", views.bulk_action, name="bulk"),
    path("<slug:slug>/add/", views.model_create, name="create"),
    path("<slug:slug>/<int:pk>/edit/", views.model_edit, name="edit"),
    path("<slug:slug>/<int:pk>/delete/", views.model_delete, name="delete"),
    path("<slug:slug>/<int:pk>/<slug:action>/", views.row_action, name="action"),
]
