# Owner: Alyan Khowaja (requests, history, contact and info pages)
from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("team/", TemplateView.as_view(template_name="team.html"), name="team"),
    path("contact/", views.contact, name="contact"),
    path("history/", views.history, name="history"),
    path("history/export.csv", views.history_export, name="history_export"),
    path("request/send/<int:profile_id>/", views.send_request, name="send_request"),
    path("requests/", views.request_inbox, name="request_inbox"),
    path("requests/<int:pk>/accept/", views.accept_request, name="accept_request"),
    path("requests/<int:pk>/decline/", views.decline_request, name="decline_request"),
    path("requests/<int:pk>/withdraw/", views.withdraw_request, name="withdraw_request"),
    path("faq/", TemplateView.as_view(template_name="faq.html"), name="faq"),

]