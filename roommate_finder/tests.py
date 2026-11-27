"""Tests for the extra features: navbar badge, request emails, dark mode, CSV helper,
profile completeness, score breakdown, compare page, sorting and CSV downloads."""
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import LifestylePreference
from matches.models import RoommateRequest
from profiles.completeness import profile_completeness
from profiles.matching import compatibility_score, score_breakdown
from profiles.models import Area, Profile, SavedProfile
from profiles.tests import make_student

from .csv_utils import safe_cell

PASSWORD = "Pass12345!"
FAST = override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])


@FAST
class NavbarBadgeAndEmailTests(TestCase):
    def setUp(self):
        self.a, self.pa = make_student("alice")
        self.b, self.pb = make_student("bob")

    def test_badge_counts_only_pending_requests_received(self):
        RoommateRequest.objects.create(sender=self.b, receiver=self.a)
        self.client.login(username="alice@example.com", password=PASSWORD)
        response = self.client.get(reverse("about"))
        self.assertEqual(response.context["pending_requests"], 1)
        self.assertContains(response, "Pending requests waiting for you")

    def test_no_badge_for_sender_or_guest(self):
        RoommateRequest.objects.create(sender=self.b, receiver=self.a)
        self.client.login(username="bob@example.com", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("about")).context["pending_requests"], 0)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("about")).context["pending_requests"], 0)

    def test_badge_disappears_after_accepting(self):
        req = RoommateRequest.objects.create(sender=self.b, receiver=self.a)
        self.client.login(username="alice@example.com", password=PASSWORD)
        self.client.post(reverse("accept_request", args=[req.pk]))
        self.assertEqual(self.client.get(reverse("about")).context["pending_requests"], 0)

    def test_new_request_sends_email_to_receiver(self):
        self.client.login(username="bob@example.com", password=PASSWORD)
        self.client.post(reverse("send_request", args=[self.pa.pk]), {"message": "Hi Alice, want to share?"})
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["alice@example.com"])
        self.assertIn("Bob", message.subject)
        self.assertIn("want to share", message.body)
        self.assertIn("/matches/requests/", message.body)

    def test_accept_and_decline_email_the_sender_but_withdraw_does_not(self):
        req = RoommateRequest.objects.create(sender=self.b, receiver=self.a)
        self.client.login(username="alice@example.com", password=PASSWORD)
        self.client.post(reverse("accept_request", args=[req.pk]))
        self.assertEqual([m.to for m in mail.outbox], [["bob@example.com"]])
        self.assertIn("accepted", mail.outbox[0].subject)
        mail.outbox.clear()
        req2 = RoommateRequest.objects.create(sender=self.a, receiver=self.b)
        self.client.logout()
        self.client.login(username="alice@example.com", password=PASSWORD)
        self.client.post(reverse("withdraw_request", args=[req2.pk]))
        self.assertEqual(mail.outbox, [])


class DarkModeTests(TestCase):
    def test_default_is_light(self):
        self.assertContains(self.client.get(reverse("about")), 'data-bs-theme="light"')

    def test_cookie_sets_dark(self):
        self.client.cookies["theme"] = "dark"
        html = self.client.get(reverse("about")).content.decode()
        self.assertIn('<html lang="en" data-bs-theme="dark">', html)
        self.assertIn('id="themeToggle"', html)

    def test_bad_cookie_value_falls_back_to_light(self):
        self.client.cookies["theme"] = "<script>"
        self.assertContains(self.client.get(reverse("about")), 'data-bs-theme="light"')


class CsvHelperTests(TestCase):
    def test_formula_characters_are_neutralised(self):
        for bad in ("=1+1", "+cmd", "-2", "@SUM(A1)"):
            self.assertTrue(safe_cell(bad).startswith("'"))
        self.assertEqual(safe_cell("Normal"), "Normal")
        self.assertEqual(safe_cell(None), "")


@FAST
class CompletenessTests(TestCase):
    def test_bare_profile_is_partly_complete(self):
        _, p = make_student("sam", bio="", program="", lifestyle=False)
        result = profile_completeness(p)
        self.assertEqual(result["percent"], 20)
        labels = [m["label"] for m in result["missing"]]
        self.assertIn("Profile photo", labels)
        self.assertIn("Verified student ID", labels)

    def test_full_profile_is_100(self):
        area = Area.objects.create(name="Downtown")
        _, p = make_student("full", area=area, verified=True)
        p.phone = "519-555-0000"
        p.photo = "profile_photos/x.png"
        self.assertEqual(profile_completeness(p)["percent"], 100)
        self.assertEqual(profile_completeness(p)["missing"], [])

    def test_meter_shows_on_own_profile_only(self):
        me, mine = make_student("me", lifestyle=False)
        other, theirs = make_student("them")
        self.client.login(username="me@example.com", password=PASSWORD)
        self.assertContains(self.client.get(reverse("profile_detail", args=[mine.pk])), "Profile completeness")
        self.assertNotContains(self.client.get(reverse("profile_detail", args=[theirs.pk])), "Profile completeness")

    def test_home_shows_nudge_until_complete(self):
        make_student("me", lifestyle=False)
        self.client.login(username="me@example.com", password=PASSWORD)
        self.assertContains(self.client.get(reverse("home")), "complete. A fuller profile")


@FAST
class BreakdownTests(TestCase):
    def test_breakdown_total_equals_compatibility_score(self):
        _, a = make_student("a", budget=700, sleep="early", cleanliness=5, pets="has")
        _, b = make_student("b", budget=900, sleep="night", cleanliness=2, pets="no")
        breakdown = score_breakdown(a, b)
        self.assertEqual(breakdown["score"], compatibility_score(a, b))
        self.assertEqual(len(breakdown["rows"]), 7)
        self.assertEqual(sum(r["max"] for r in breakdown["rows"]), 100)

    def test_missing_lifestyle_gives_two_rows(self):
        _, a = make_student("a", lifestyle=False)
        _, b = make_student("b")
        self.assertEqual([r["label"] for r in score_breakdown(a, b)["rows"]], ["Budget", "Preferred area"])

    def test_pets_clash_row_is_zero(self):
        _, a = make_student("a", pets="has")
        _, b = make_student("b", pets="no")
        pets = [r for r in score_breakdown(a, b)["rows"] if r["label"] == "Pets"][0]
        self.assertEqual(pets["points"], 0)

    def test_detail_page_shows_breakdown_to_logged_in_user(self):
        make_student("viewer")
        _, other = make_student("other")
        self.client.login(username="viewer@example.com", password=PASSWORD)
        response = self.client.get(reverse("profile_detail", args=[other.pk]))
        self.assertContains(response, "Why you match")
        self.assertContains(response, "Sleep schedule")

    def test_guest_and_own_profile_see_no_breakdown(self):
        _, mine = make_student("viewer")
        self.assertNotContains(self.client.get(reverse("profile_detail", args=[mine.pk])), "Why you match")
        self.client.login(username="viewer@example.com", password=PASSWORD)
        self.assertNotContains(self.client.get(reverse("profile_detail", args=[mine.pk])), "Why you match")


@FAST
class SortTests(TestCase):
    def setUp(self):
        make_student("me", budget=800)
        make_student("cheap", budget=500)
        make_student("mid", budget=800)
        make_student("rich", budget=1500)

    def names(self, **params):
        self.client.login(username="me@example.com", password=PASSWORD)
        response = self.client.get(reverse("home"), params)
        return [p.full_name for p in response.context["profiles"]]

    def test_budget_low_to_high(self):
        self.assertEqual(self.names(sort="budget_low"), ["Cheap", "Mid", "Rich"])

    def test_budget_high_to_low(self):
        self.assertEqual(self.names(sort="budget_high"), ["Rich", "Mid", "Cheap"])

    def test_newest_first(self):
        self.assertEqual(self.names(sort="newest"), ["Rich", "Mid", "Cheap"])

    def test_default_is_best_match(self):
        self.assertEqual(self.names()[0], "Mid")

    def test_bad_sort_value_is_ignored(self):
        self.assertEqual(self.names(sort="drop table")[0], "Mid")

    def test_guest_can_sort_too(self):
        response = self.client.get(reverse("home"), {"sort": "budget_high"})
        self.assertEqual([p.full_name for p in response.context["profiles"]][0], "Rich")

    def test_dropdown_shows_sort_choices(self):
        self.assertContains(self.client.get(reverse("home")), "Budget: low to high")


@FAST
class CompareTests(TestCase):
    def setUp(self):
        self.me, self.mine = make_student("me")
        _, self.p1 = make_student("anna", budget=600, sleep="early")
        _, self.p2 = make_student("ben", budget=900, sleep="early", lifestyle=True)
        self.client.login(username="me@example.com", password=PASSWORD)

    def test_compare_two_profiles(self):
        response = self.client.get(reverse("compare_profiles"), {"ids": [self.p1.pk, self.p2.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "$600/month")
        self.assertContains(response, "$900/month")
        self.assertContains(response, "Match with you")

    def test_compare_never_shows_contact_details(self):
        self.p1.phone = "519-555-9999"; self.p1.save()
        response = self.client.get(reverse("compare_profiles"), {"ids": [self.p1.pk, self.p2.pk]})
        self.assertNotContains(response, "519-555-9999")
        self.assertNotContains(response, "anna@example.com")

    def test_wrong_number_of_ids_goes_back_to_shortlist(self):
        for params in ({}, {"ids": [self.p1.pk]}, {"ids": [self.p1.pk, self.p1.pk]},
                       {"ids": [self.p1.pk, self.p2.pk, self.mine.pk]}, {"ids": ["x", "y"]}):
            response = self.client.get(reverse("compare_profiles"), params)
            self.assertRedirects(response, reverse("saved_list"))

    def test_unknown_profile_is_404(self):
        self.assertEqual(self.client.get(reverse("compare_profiles"), {"ids": [self.p1.pk, 99999]}).status_code, 404)

    def test_guest_must_log_in(self):
        self.client.logout()
        response = self.client.get(reverse("compare_profiles"), {"ids": [self.p1.pk, self.p2.pk]})
        self.assertEqual(response.status_code, 302)

    def test_shortlist_shows_compare_controls_only_with_two_saved(self):
        SavedProfile.objects.create(user=self.me, profile=self.p1)
        self.assertNotContains(self.client.get(reverse("saved_list")), 'id="compareBtn"')
        SavedProfile.objects.create(user=self.me, profile=self.p2)
        self.assertContains(self.client.get(reverse("saved_list")), 'id="compareBtn"')


@FAST
class CsvDownloadTests(TestCase):
    def setUp(self):
        self.me, self.mine = make_student("me")
        _, self.p1 = make_student("anna", budget=600)
        self.p1.phone = "519-555-9999"; self.p1.save()
        SavedProfile.objects.create(user=self.me, profile=self.p1)
        self.client.login(username="me@example.com", password=PASSWORD)

    def test_shortlist_csv(self):
        response = self.client.get(reverse("saved_export"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/csv"))
        self.assertIn("shortlist.csv", response["Content-Disposition"])
        text = response.content.decode()
        self.assertIn("Name,Program", text)
        self.assertIn("Anna", text)
        self.assertNotIn("519-555-9999", text)
        self.assertNotIn("anna@example.com", text)

    def test_shortlist_csv_blocks_formula_injection(self):
        self.p1.full_name = "=HYPERLINK(\"http://evil\")"; self.p1.save()
        self.assertIn("'=HYPERLINK", self.client.get(reverse("saved_export")).content.decode())

    def test_shortlist_csv_only_includes_own_entries(self):
        other, _ = make_student("zed")
        SavedProfile.objects.create(user=other, profile=self.mine)
        self.assertNotIn("Me,", self.client.get(reverse("saved_export")).content.decode().split("\n", 1)[1])

    def test_history_csv(self):
        self.client.get(reverse("about"))
        response = self.client.get(reverse("history_export"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("my_history.csv", response["Content-Disposition"])
        self.assertIn("/matches/about/", response.content.decode())

    def test_downloads_need_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("saved_export")).status_code, 302)
        self.assertEqual(self.client.get(reverse("history_export")).status_code, 302)

    def test_download_buttons_are_visible(self):
        self.assertContains(self.client.get(reverse("saved_list")), "Download CSV")
        self.assertContains(self.client.get(reverse("history")), "Download CSV")
