# Owner: Alyan Khowaja (requests, history, contact and info pages)
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    # Placeholder pages so the footer links work. Replace as you build them.
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
    path("contact/", TemplateView.as_view(template_name="contact.html"), name="contact"),
    path("team/", TemplateView.as_view(template_name="team.html"), name="team"),
]
