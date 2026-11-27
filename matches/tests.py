# Owner: Alyan Khowaja
"""Tests for matches: roommate requests, visit tracking, History page, contact form, info pages."""
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from profiles.models import Profile

from .models import ContactMessage, RoommateRequest, VisitLog

User = get_user_model()
PASSWORD = "Pass12345!"
# Fast password hashing so the tests run in seconds (tests only, not the real site)
FAST = override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])


def make_student(username, with_profile=True):
    user = User.objects.create_user(f"{username}@example.com", PASSWORD)
    profile = None
    if with_profile:
        profile = Profile.objects.create(
            user=user, full_name=username.title(), budget=700, phone="519-555-0100"
        )
    return user, profile


@FAST
class RoommateRequestTests(TestCase):
    def setUp(self):
        self.alyan, self.alyan_profile = make_student("alyan")
        self.sam, self.sam_profile = make_student("sam")
        self.client.login(username="alyan@example.com", password=PASSWORD)
        self.send_url = reverse("send_request", args=[self.sam_profile.pk])

    def test_pages_require_login(self):
        self.client.logout()
        for url in (self.send_url, reverse("request_inbox")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("login", response["Location"])

    def test_send_request_creates_pending_request(self):
        response = self.client.post(self.send_url, {"message": "Hi Sam!"})
        self.assertRedirects(response, reverse("request_inbox"))
        req = RoommateRequest.objects.get()
        self.assertEqual((req.sender, req.receiver, req.status), (self.alyan, self.sam, "pending"))

    def test_request_with_empty_message_is_allowed(self):
        self.client.post(self.send_url, {"message": ""})
        self.assertEqual(RoommateRequest.objects.count(), 1)

    def test_cannot_send_request_to_yourself(self):
        response = self.client.post(reverse("send_request", args=[self.alyan_profile.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(RoommateRequest.objects.count(), 0)

    def test_duplicate_request_is_blocked(self):
        self.client.post(self.send_url, {"message": "one"})
        self.client.post(self.send_url, {"message": "two"})
        self.assertEqual(RoommateRequest.objects.count(), 1)

    def test_can_ask_again_after_decline(self):
        self.client.post(self.send_url)
        RoommateRequest.objects.update(status="declined")
        self.client.post(self.send_url)
        self.assertEqual(RoommateRequest.objects.count(), 2)

    def test_unknown_profile_returns_404(self):
        self.assertEqual(self.client.get(reverse("send_request", args=[9999])).status_code, 404)

    def test_user_without_profile_must_create_one_first(self):
        make_student("newbie", with_profile=False)
        self.client.login(username="newbie@example.com", password=PASSWORD)
        self.assertRedirects(self.client.get(self.send_url), reverse("profile_create"))

    def test_database_blocks_self_request_and_duplicates(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RoommateRequest.objects.create(sender=self.alyan, receiver=self.alyan)
        RoommateRequest.objects.create(sender=self.alyan, receiver=self.sam)
        with self.assertRaises(IntegrityError), transaction.atomic():
            RoommateRequest.objects.create(sender=self.alyan, receiver=self.sam)

    def test_receiver_can_accept_and_contact_becomes_visible(self):
        self.client.post(self.send_url)
        req = RoommateRequest.objects.get()
        sam = Client()
        sam.login(username="sam@example.com", password=PASSWORD)
        alyan_profile_url = reverse("profile_detail", args=[self.alyan_profile.pk])
        self.assertNotContains(sam.get(alyan_profile_url), "alyan@example.com")
        sam.post(reverse("accept_request", args=[req.pk]))
        req.refresh_from_db()
        self.assertEqual(req.status, "accepted")
        self.assertIsNotNone(req.responded_at)
        self.assertContains(sam.get(alyan_profile_url), "alyan@example.com")
        self.assertContains(
            self.client.get(reverse("profile_detail", args=[self.sam_profile.pk])), "sam@example.com"
        )

    def test_receiver_can_decline(self):
        self.client.post(self.send_url)
        req = RoommateRequest.objects.get()
        sam = Client()
        sam.login(username="sam@example.com", password=PASSWORD)
        sam.post(reverse("decline_request", args=[req.pk]))
        req.refresh_from_db()
        self.assertEqual(req.status, "declined")

    def test_sender_can_withdraw(self):
        self.client.post(self.send_url)
        req = RoommateRequest.objects.get()
        self.client.post(reverse("withdraw_request", args=[req.pk]))
        req.refresh_from_db()
        self.assertEqual(req.status, "withdrawn")

    def test_sender_cannot_accept_own_request(self):
        self.client.post(self.send_url)
        req = RoommateRequest.objects.get()
        response = self.client.post(reverse("accept_request", args=[req.pk]))
        self.assertEqual(response.status_code, 404)
        req.refresh_from_db()
        self.assertEqual(req.status, "pending")

    def test_third_person_cannot_change_a_request(self):
        self.client.post(self.send_url)
        req = RoommateRequest.objects.get()
        make_student("eve")
        eve = Client()
        eve.login(username="eve@example.com", password=PASSWORD)
        for name in ("accept_request", "decline_request", "withdraw_request"):
            self.assertEqual(eve.post(reverse(name, args=[req.pk])).status_code, 404, name)
        req.refresh_from_db()
        self.assertEqual(req.status, "pending")

    def test_actions_only_work_with_post(self):
        self.client.post(self.send_url)
        req = RoommateRequest.objects.get()
        sam = Client()
        sam.login(username="sam@example.com", password=PASSWORD)
        self.assertEqual(sam.get(reverse("accept_request", args=[req.pk])).status_code, 405)

    def test_cannot_respond_to_a_request_twice(self):
        self.client.post(self.send_url)
        req = RoommateRequest.objects.get()
        sam = Client()
        sam.login(username="sam@example.com", password=PASSWORD)
        sam.post(reverse("decline_request", args=[req.pk]))
        self.assertEqual(sam.post(reverse("accept_request", args=[req.pk])).status_code, 404)

    def test_inbox_shows_sent_and_received(self):
        self.client.post(self.send_url)
        self.assertContains(self.client.get(reverse("request_inbox")), "Sam")
        sam = Client()
        sam.login(username="sam@example.com", password=PASSWORD)
        self.assertContains(sam.get(reverse("request_inbox")), "Alyan")


@FAST
class VisitTrackingTests(TestCase):
    def setUp(self):
        self.user, self.profile = make_student("alyan")

    def test_page_views_are_logged_for_guests(self):
        self.client.get(reverse("home"))
        log = VisitLog.objects.get()
        self.assertIsNone(log.user)
        self.assertEqual(log.path, "/")
        self.assertTrue(log.session_key)

    def test_page_views_are_logged_for_users(self):
        self.client.login(username="alyan@example.com", password=PASSWORD)
        self.client.get(reverse("home"))
        self.assertEqual(VisitLog.objects.filter(user=self.user).count(), 1)

    def test_admin_static_post_and_errors_are_not_logged(self):
        self.client.get("/admin/login/")
        self.client.get("/static/css/style.css")
        self.client.post(reverse("contact"), {})
        self.client.get("/profile/9999/")
        self.assertEqual(VisitLog.objects.count(), 0)

    def test_last_visit_cookie_set_on_first_request_only(self):
        first = self.client.get(reverse("home"))
        self.assertIn("last_visit", first.cookies)
        self.assertTrue(first.cookies["last_visit"].value.isdigit())
        second = self.client.get(reverse("home"))
        self.assertNotIn("last_visit", second.cookies)

    def test_recently_viewed_keeps_newest_first_without_duplicates(self):
        others = [make_student(f"s{i}")[1] for i in range(3)]
        for p in (others[0], others[1], others[2], others[0]):
            self.client.get(reverse("profile_detail", args=[p.pk]))
        self.assertEqual(
            self.client.session["recent_profiles"], [others[0].pk, others[2].pk, others[1].pk]
        )

    def test_recently_viewed_is_capped_at_five(self):
        for i in range(7):
            p = make_student(f"s{i}")[1]
            self.client.get(reverse("profile_detail", args=[p.pk]))
        self.assertEqual(len(self.client.session["recent_profiles"]), 5)


@FAST
class HistoryPageTests(TestCase):
    def setUp(self):
        self.user, self.profile = make_student("alyan")
        self.other = make_student("sam")[1]

    def test_requires_login(self):
        response = self.client.get(reverse("history"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_first_time_visitor_sees_friendly_empty_state(self):
        self.client.login(username="alyan@example.com", password=PASSWORD)
        response = self.client.get(reverse("history"))
        self.assertContains(response, "first visit")
        self.assertContains(response, "haven't viewed any profiles")

    def test_shows_page_views_per_day_and_recently_viewed(self):
        self.client.login(username="alyan@example.com", password=PASSWORD)
        self.client.get(reverse("home"))
        self.client.get(reverse("profile_detail", args=[self.other.pk]))
        response = self.client.get(reverse("history"))
        self.assertContains(response, "Sam")
        self.assertTrue(len(response.context["visits_per_day"]) >= 1)
        # home + profile page; the History page itself is counted after it is shown
        self.assertEqual(response.context["visits_per_day"][0]["count"], 2)

    def test_returning_visitor_sees_last_visit_date(self):
        self.client.cookies["last_visit"] = "1577854800"  # 2020-01-01
        self.client.login(username="alyan@example.com", password=PASSWORD)
        response = self.client.get(reverse("history"))
        self.assertContains(response, "Jan 1, 2020")
        self.assertNotContains(response, "first visit")

    def test_garbage_cookie_does_not_crash(self):
        self.client.cookies["last_visit"] = "not-a-number"
        self.client.login(username="alyan@example.com", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("history")).status_code, 200)

    def test_history_only_counts_own_visits(self):
        sam = Client()
        sam.login(username="sam@example.com", password=PASSWORD)
        for _ in range(4):
            sam.get(reverse("home"))
        self.client.login(username="alyan@example.com", password=PASSWORD)
        self.client.get(reverse("home"))
        response = self.client.get(reverse("history"))
        self.assertEqual(response.context["visits_per_day"][0]["count"], 1)


class ContactFormTests(TestCase):
    valid = {"name": "Visitor", "email": "v@example.com", "subject": "Hello",
             "message": "I have a question about verification."}

    def test_page_loads_for_guests(self):
        self.assertEqual(self.client.get(reverse("contact")).status_code, 200)

    def test_empty_form_shows_errors_and_saves_nothing(self):
        response = self.client.post(reverse("contact"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "required", html=False)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_each_empty_field_is_rejected(self):
        for field in self.valid:
            response = self.client.post(reverse("contact"), {**self.valid, field: ""})
            self.assertEqual(response.status_code, 200, field)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_invalid_email_rejected(self):
        self.client.post(reverse("contact"), {**self.valid, "email": "not-an-email"})
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_short_message_rejected(self):
        response = self.client.post(reverse("contact"), {**self.valid, "message": "short"})
        self.assertContains(response, "at least 10")
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_valid_message_is_saved_with_thanks(self):
        response = self.client.post(reverse("contact"), self.valid, follow=True)
        self.assertContains(response, "Thanks")
        msg = ContactMessage.objects.get()
        self.assertEqual((msg.name, msg.is_resolved), ("Visitor", False))

    @FAST
    def test_form_is_prefilled_for_logged_in_users(self):
        make_student("alyan")
        self.client.login(username="alyan@example.com", password=PASSWORD)
        self.assertContains(self.client.get(reverse("contact")), "alyan@example.com")


class InfoPagesTests(TestCase):
    def test_public_pages_load(self):
        for name in ("about", "team", "faq", "contact"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_footer_links_to_info_pages(self):
        html = self.client.get(reverse("home")).content.decode()
        for name in ("about", "team", "faq", "contact"):
            self.assertIn(reverse(name), html, name)
