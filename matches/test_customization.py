# Owner: Alyan Khowaja
"""Tests for the editable pages, the customization settings and the performance changes."""
from datetime import timedelta
from io import StringIO

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from .models import FAQItem, InfoPage, RoommateRequest, TeamMember, VisitLog
from .tests import FAST, PASSWORD, User, make_student


class EditableInfoPagesTests(TestCase):
    def test_seeded_content_shows_on_the_pages(self):
        self.assertContains(self.client.get(reverse("about")), "Finding a good roommate is hard")
        self.assertContains(self.client.get(reverse("team")), "Alyan Khowaja")
        self.assertContains(self.client.get(reverse("faq")), "Who can see my student ID?")

    def test_editing_a_faq_changes_the_page_and_hides_unpublished(self):
        FAQItem.objects.all().delete()
        FAQItem.objects.create(question="Is it free?", answer="Yes.\nAlways.", order=1)
        FAQItem.objects.create(question="Secret?", answer="No.", order=2, is_published=False)
        html = self.client.get(reverse("faq")).content.decode()
        self.assertIn("Is it free?", html)
        self.assertIn("Yes.<br>Always.", html)
        self.assertNotIn("Secret?", html)

    def test_order_field_controls_team_order_and_inactive_are_hidden(self):
        TeamMember.objects.all().delete()
        TeamMember.objects.create(name="Zed", role="Last", order=2)
        TeamMember.objects.create(name="Amy", role="First", order=1)
        TeamMember.objects.create(name="Gone", role="Left", order=0, is_active=False)
        response = self.client.get(reverse("team"))
        self.assertEqual([m.name for m in response.context["members"]], ["Amy", "Zed"])
        self.assertNotContains(response, "Gone")

    def test_french_text_is_used_when_present_and_english_is_the_fallback(self):
        FAQItem.objects.all().delete()
        FAQItem.objects.create(question="Q1", question_fr="Question un", answer="A1", answer_fr="Réponse un")
        FAQItem.objects.create(question="Q2", answer="A2")  # no French written
        with translation.override("fr"):
            html = self.client.get(reverse("faq"), HTTP_ACCEPT_LANGUAGE="fr").content.decode()
        self.assertIn("Question un", html)
        self.assertIn("Réponse un", html)
        self.assertIn("Q2", html)

    def test_about_paragraphs_split_on_blank_lines(self):
        InfoPage.objects.filter(slug="about").update(title="Hi", body="One\n\nTwo\n\n\nThree")
        response = self.client.get(reverse("about"))
        self.assertEqual(response.context["page"].paragraphs, ["One", "Two", "Three"])

    def test_about_page_survives_a_deleted_row(self):
        InfoPage.objects.all().delete()
        self.assertEqual(self.client.get(reverse("about")).status_code, 200)

    @FAST
    def test_staff_can_edit_content_in_the_panel(self):
        User.objects.create_user("staff@example.com", PASSWORD, is_staff=True)
        self.client.login(username="staff@example.com", password=PASSWORD)
        for slug in ("about", "team", "faq"):
            self.assertEqual(self.client.get(reverse("panel:list", args=[slug])).status_code, 200)
        response = self.client.post(reverse("panel:create", args=["faq"]), {
            "question": "New?", "question_fr": "", "answer": "Yes", "answer_fr": "", "order": 9,
            "is_published": "on"})
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(reverse("faq")), "New?")

    @FAST
    def test_panel_content_requires_staff(self):
        make_student("plain")
        self.client.login(username="plain@example.com", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("panel:list", args=["faq"])).status_code, 403)


class SiteCustomizationTests(TestCase):
    def test_theme_values_become_css_variables(self):
        with override_settings(SITE_THEME={"coral": "#123456", "radius": "1rem"}):
            html = self.client.get(reverse("home")).content.decode()
        self.assertIn("--rf-coral:#123456", html)
        self.assertIn("--rf-radius:1rem", html)
        self.assertIn("--rf-navy:#1E3A5F", html)  # unset keys keep their defaults

    def test_footer_comes_from_settings_and_empty_social_links_are_hidden(self):
        self.assertNotContains(self.client.get(reverse("about")), "bi-facebook")
        with override_settings(SITE_FOOTER={"location": "Toronto, ON", "credit": "Demo",
                                            "social": {"instagram": "https://example.com/ig"}}):
            html = self.client.get(reverse("about")).content.decode()
        self.assertIn("Toronto, ON", html)
        self.assertIn("https://example.com/ig", html)
        self.assertIn("bi-instagram", html)
        self.assertNotIn("bi-facebook", html)

    def test_site_name_and_support_email_are_used(self):
        with override_settings(SITE_NAME="FlatMates", SUPPORT_EMAIL="help@flat.example"):
            html = self.client.get(reverse("about")).content.decode()
        self.assertIn("FlatMates", html)
        self.assertIn("mailto:help@flat.example", html)

    def test_footer_tagline_is_still_translated(self):
        from django.utils.html import escape

        english = "Helping University of Windsor students find roommates they'll actually get along with."
        with override_settings(SITE_FOOTER={"tagline": english}):
            html = self.client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="fr").content.decode()
        with translation.override("fr"):
            french = translation.gettext(english)
        self.assertNotEqual(french, english)
        self.assertIn(escape(french), html)


@FAST
class VisitTrackingSettingsTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_rapid_refresh_of_the_same_page_is_counted_once(self):
        self.client.get(reverse("about"))
        self.client.get(reverse("about"))
        self.assertEqual(VisitLog.objects.count(), 1)

    def test_dedupe_can_be_switched_off(self):
        with override_settings(VISIT_TRACKING={"DEDUPE_SECONDS": 0}):
            self.client.get(reverse("about"))
            self.client.get(reverse("about"))
        self.assertEqual(VisitLog.objects.count(), 2)

    def test_different_pages_are_each_counted(self):
        self.client.get(reverse("about"))
        self.client.get(reverse("faq"))
        self.assertEqual(VisitLog.objects.count(), 2)

    def test_tracking_can_be_disabled(self):
        with override_settings(VISIT_TRACKING={"ENABLED": False}):
            self.client.get(reverse("about"))
        self.assertEqual(VisitLog.objects.count(), 0)
        self.assertNotIn("last_visit", self.client.cookies)

    def test_recent_profile_limit_is_configurable(self):
        profiles = [make_student(f"p{i}")[1] for i in range(4)]
        with override_settings(VISIT_TRACKING={"RECENT_PROFILES": 2}):
            for p in profiles:
                self.client.get(reverse("profile_detail", args=[p.pk]))
        self.assertEqual(len(self.client.session["recent_profiles"]), 2)

    def test_csv_and_non_html_responses_are_not_logged(self):
        make_student("alyan")
        self.client.login(username="alyan@example.com", password=PASSWORD)
        VisitLog.objects.all().delete()
        self.client.get(reverse("history_export"))
        self.assertEqual(VisitLog.objects.count(), 0)

    def test_prune_command_deletes_only_old_rows(self):
        old = VisitLog.objects.create(path="/old/")
        VisitLog.objects.filter(pk=old.pk).update(visited_at=timezone.now() - timedelta(days=400))
        VisitLog.objects.create(path="/new/")
        out = StringIO()
        call_command("prune_visits", "--days", "30", stdout=out)
        self.assertEqual(list(VisitLog.objects.values_list("path", flat=True)), ["/new/"])
        self.assertIn("Deleted 1", out.getvalue())


@FAST
class HistoryRangeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user, _ = make_student("alyan")
        self.client.login(username="alyan@example.com", password=PASSWORD)
        for days_ago in (1, 10, 40):
            visit = VisitLog.objects.create(user=self.user, path=f"/d{days_ago}/")
            VisitLog.objects.filter(pk=visit.pk).update(visited_at=timezone.now() - timedelta(days=days_ago))

    def rows(self, url):
        response = self.client.get(url)
        return response, sum(v["count"] for v in response.context["visits_per_day"])

    def test_default_is_seven_days(self):
        response, total = self.rows(reverse("history"))
        self.assertEqual(response.context["days"], 7)
        self.assertEqual(total, 1)

    def test_choosing_a_longer_range_shows_more(self):
        # (viewing History is itself logged, so compare the ranges against each other)
        week = self.rows(reverse("history") + "?days=7")[1]
        fortnight = self.rows(reverse("history") + "?days=14")[1]
        quarter = self.rows(reverse("history") + "?days=90")[1]
        self.assertGreater(fortnight, week)   # the 10-day-old visit appears
        self.assertGreater(quarter, fortnight)  # and so does the 40-day-old one

    def test_choice_is_remembered_for_next_time(self):
        self.client.get(reverse("history") + "?days=30")
        response, _ = self.rows(reverse("history"))
        self.assertEqual(response.context["days"], 30)

    def test_invalid_range_falls_back_to_default(self):
        for bad in ("abc", "-5", "999", ""):
            self.assertEqual(self.client.get(reverse("history") + f"?days={bad}").context["days"], 7)

    @override_settings(HISTORY_DAY_CHOICES=(3, 5), HISTORY_DEFAULT_DAYS=3)
    def test_choices_and_default_come_from_settings(self):
        response = self.client.get(reverse("history"))
        self.assertEqual(response.context["day_choices"], (3, 5))
        self.assertEqual(response.context["days"], 3)
        self.assertEqual(self.client.get(reverse("history") + "?days=7").context["days"], 3)


@FAST
class RequestInboxTests(TestCase):
    def setUp(self):
        cache.clear()
        self.me, self.me_profile = make_student("me")
        self.client.login(username="me@example.com", password=PASSWORD)

    def make_requests(self, count, status="pending"):
        start = User.objects.count()
        for i in range(start, start + count):
            other, _ = make_student(f"other{status}{i}")
            RoommateRequest.objects.create(sender=other, receiver=self.me, status=status)

    def test_status_filter_limits_both_lists(self):
        self.make_requests(2, "pending")
        self.make_requests(1, "declined")
        response = self.client.get(reverse("request_inbox") + "?status=declined")
        self.assertEqual(len(response.context["received_page"]), 1)
        self.assertEqual(response.context["status"], "declined")

    def test_unknown_status_shows_everything(self):
        self.make_requests(2)
        response = self.client.get(reverse("request_inbox") + "?status=bogus")
        self.assertEqual(len(response.context["received_page"]), 2)
        self.assertEqual(response.context["status"], "")

    @override_settings(REQUESTS_PAGE_SIZE=2)
    def test_pagination_uses_the_page_size_setting(self):
        self.make_requests(5)
        first = self.client.get(reverse("request_inbox"))
        self.assertEqual(len(first.context["received_page"]), 2)
        self.assertContains(first, "Page 1 of 3")
        last = self.client.get(reverse("request_inbox") + "?page_received=3")
        self.assertEqual(len(last.context["received_page"]), 1)

    def test_pagination_links_keep_the_filter(self):
        with override_settings(REQUESTS_PAGE_SIZE=1):
            self.make_requests(3)
            response = self.client.get(reverse("request_inbox") + "?status=pending")
        self.assertContains(response, "status=pending&amp;page_received=2".replace("&amp;", "&"))

    def queries_for_inbox(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            self.client.get(reverse("request_inbox"))
        return len(ctx)

    def test_inbox_query_count_does_not_grow_with_requests(self):
        self.make_requests(1)
        self.queries_for_inbox()  # warm-up: the first request also creates the visit-tracking session
        few = self.queries_for_inbox()
        self.make_requests(8)
        self.assertEqual(self.queries_for_inbox(), few)


@FAST
class SendRequestSafetyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.me, _ = make_student("me")
        self.other, self.other_profile = make_student("other")
        self.client.login(username="me@example.com", password=PASSWORD)
        self.url = reverse("send_request", args=[self.other_profile.pk])

    def test_cannot_send_when_they_already_sent_you_a_pending_request(self):
        RoommateRequest.objects.create(sender=self.other, receiver=self.me)
        response = self.client.post(self.url, {"message": "hi"}, follow=True)
        self.assertEqual(RoommateRequest.objects.count(), 1)
        self.assertContains(response, "already sent you a request")

    def test_can_send_after_their_request_was_declined(self):
        RoommateRequest.objects.create(sender=self.other, receiver=self.me, status="declined")
        self.client.post(self.url, {"message": "hi"})
        self.assertEqual(RoommateRequest.objects.filter(sender=self.me).count(), 1)

    def test_double_submit_is_handled_without_a_server_error(self):
        from unittest import mock

        RoommateRequest.objects.create(sender=self.me, receiver=self.other, status="pending")
        # Simulate losing the race: the pre-check passes but the unique constraint fires on save
        with mock.patch("matches.views.RoommateRequest.objects.filter") as patched:
            patched.return_value.only.return_value = []
            response = self.client.post(self.url, {"message": "again"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RoommateRequest.objects.filter(sender=self.me).count(), 1)
        self.assertContains(response, "already have an active request")
