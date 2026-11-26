# Owner: Alyan Khowaja (requests, history, contact and info pages)
from django.urls import path

from . import views

urlpatterns = [
    path("about/", views.about, name="about"),
    path("team/", views.team, name="team"),
    path("contact/", views.contact, name="contact"),
    path("history/", views.history, name="history"),
    path("history/export.csv", views.history_export, name="history_export"),
    path("request/send/<int:profile_id>/", views.send_request, name="send_request"),
    path("requests/", views.request_inbox, name="request_inbox"),
    path("requests/<int:pk>/accept/", views.accept_request, name="accept_request"),
    path("requests/<int:pk>/decline/", views.decline_request, name="decline_request"),
    path("requests/<int:pk>/withdraw/", views.withdraw_request, name="withdraw_request"),
    path("faq/", views.faq, name="faq"),
]