# Owner: Mohammed Adil (profiles, search, matching, saved shortlist)
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    # Placeholder home page. Replace with the home ListView.
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
