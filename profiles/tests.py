# Owner: Mohammed Adil
"""Tests for profiles: compatibility score, home page search/filters, profile page, shortlist."""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import LifestylePreference
from matches.models import RoommateRequest

from .matching import compatibility_score
from .models import Area, Profile, SavedProfile

User = get_user_model()
PASSWORD = "Pass12345!"
# Fast password hashing so the tests run in seconds (tests only, not the real site)
FAST = override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])


def make_student(username, budget=700, area=None, sleep="flexible", cleanliness=3, pets="ok",
                 smoking="no", guests="no", verified=False, lifestyle=True,
                 program="Computer Science", bio="Quiet student"):
    user = User.objects.create_user(f"{username}@example.com", PASSWORD)
    profile = Profile.objects.create(
        user=user, full_name=username.title(), program=program, bio=bio, budget=budget,
        preferred_area=area, is_verified=verified,
    )
    if lifestyle:
        LifestylePreference.objects.create(
            profile=profile, sleep_schedule=sleep, cleanliness=cleanliness, pets=pets,
            smoking=smoking, guests_often=guests,
        )
    return user, Profile.objects.select_related("lifestyle", "user").get(pk=profile.pk)


@FAST
class CompatibilityScoreTests(TestCase):
    def setUp(self):
        self.area = Area.objects.create(name="Downtown")
        self.other_area = Area.objects.create(name="Sandwich")

    def test_identical_profiles_score_100(self):
        _, a = make_student("ann", area=self.area)
        _, b = make_student("bob", area=self.area)
        self.assertEqual(compatibility_score(a, b), 100)

    def test_score_is_symmetric(self):
        _, a = make_student("ann", budget=500, area=self.area, sleep="early")
        _, b = make_student("bob", budget=900, area=self.other_area, sleep="night")
        self.assertEqual(compatibility_score(a, b), compatibility_score(b, a))

    def test_score_always_between_0_and_100(self):
        _, a = make_student("ann", budget=1, area=self.area, sleep="early", cleanliness=1,
                            pets="has", smoking="yes", guests="yes")
        _, b = make_student("bob", budget=100000, area=self.other_area, sleep="night",
                            cleanliness=5, pets="no", smoking="no", guests="no")
        self.assertTrue(0 <= compatibility_score(a, b) <= 100)

    def test_bigger_budget_gap_lowers_score(self):
        _, a = make_student("ann", budget=700, area=self.area)
        _, near = make_student("near", budget=750, area=self.area)
        _, far = make_student("far", budget=2000, area=self.area)
        self.assertGreater(compatibility_score(a, near), compatibility_score(a, far))

    def test_same_area_scores_higher_than_different_area(self):
        _, a = make_student("ann", area=self.area)
        _, same = make_student("same", area=self.area)
        _, diff = make_student("diff", area=self.other_area)
        self.assertGreater(compatibility_score(a, same), compatibility_score(a, diff))

    def test_flexible_sleeper_is_partial_match(self):
        _, early = make_student("early", sleep="early")
        _, early2 = make_student("early2", sleep="early")
        _, flex = make_student("flex", sleep="flexible")
        _, night = make_student("night", sleep="night")
        full = compatibility_score(early, early2)
        partial = compatibility_score(early, flex)
        none = compatibility_score(early, night)
        self.assertTrue(full > partial > none)

    def test_pets_clash_lowers_score(self):
        _, has = make_student("has", pets="has")
        _, no_pets = make_student("nopets", pets="no")
        _, fine = make_student("fine", pets="ok")
        self.assertGreater(compatibility_score(has, fine), compatibility_score(has, no_pets))

    def test_missing_lifestyle_uses_budget_and_area_only(self):
        _, a = make_student("ann", area=self.area, lifestyle=False)
        _, b = make_student("bob", area=self.area, lifestyle=False)
        self.assertEqual(compatibility_score(a, b), 100)
        _, c = make_student("cat", area=self.other_area, lifestyle=False)
        self.assertEqual(compatibility_score(a, c), 67)


@FAST
class HomeViewTests(TestCase):
    def setUp(self):
        self.downtown = Area.objects.create(name="Downtown")
        self.sandwich = Area.objects.create(name="Sandwich")
        self.me, self.my_profile = make_student("viewer", budget=700, area=self.downtown, sleep="early")

    def names(self, response):
        return [p.user.email.split("@")[0] for p in response.context["profiles"]]

    def test_guest_sees_at_most_six_profiles(self):
        for i in range(8):
            make_student(f"s{i}")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["profiles"]), 6)

    def test_guest_sees_login_prompt_and_blur(self):
        make_student("s1")
        html = self.client.get(reverse("home")).content.decode()
        self.assertIn("Log in to see match", html)
        self.assertIn("Sign up &amp; verify", html)
        self.assertIn("browsing as a guest", html)

    def test_search_with_no_results_shows_message(self):
        make_student("s1")
        response = self.client.get(reverse("home"), {"q": "nobodyhasthisname"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No profiles match your search")

    def test_blank_search_returns_everyone(self):
        make_student("s1")
        make_student("s2")
        response = self.client.get(reverse("home"), {"q": "   "})
        self.assertEqual(len(response.context["profiles"]), 3)

    def test_keyword_search_matches_program(self):
        make_student("eng", program="Mechanical Engineering")
        make_student("bio", program="Biology")
        response = self.client.get(reverse("home"), {"q": "engineering"})
        self.assertEqual(self.names(response), ["eng"])

    def test_invalid_filter_values_are_ignored(self):
        make_student("s1")
        base = len(self.client.get(reverse("home")).context["profiles"])
        response = self.client.get(
            reverse("home"), {"budget": "abc", "area": "abc", "lifestyle": "x"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["profiles"]), base)
        response = self.client.get(reverse("home"), {"area": "99999999999999"})
        self.assertEqual(response.status_code, 200)

    def test_budget_filter(self):
        make_student("cheap", budget=500)
        make_student("mid", budget=800)
        make_student("rich", budget=1500)
        self.assertEqual(self.names(self.client.get(reverse("home"), {"budget": "under_600"})), ["cheap"])
        self.assertEqual(self.names(self.client.get(reverse("home"), {"budget": "over_1200"})), ["rich"])
        self.assertEqual(
            sorted(self.names(self.client.get(reverse("home"), {"budget": "600_900"}))),
            ["mid", "viewer"],
        )

    def test_area_filter(self):
        make_student("sw", area=self.sandwich)
        response = self.client.get(reverse("home"), {"area": self.sandwich.pk})
        self.assertEqual(self.names(response), ["sw"])

    def test_lifestyle_filter(self):
        make_student("owl", sleep="night")
        response = self.client.get(reverse("home"), {"lifestyle": "night"})
        self.assertEqual(self.names(response), ["owl"])

    def test_logged_in_user_does_not_see_own_profile(self):
        make_student("other")
        self.client.login(username="viewer@example.com", password=PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertNotIn("viewer", self.names(response))

    def test_logged_in_results_ranked_by_match(self):
        make_student("far", budget=2000, area=self.sandwich, sleep="night")
        make_student("close", budget=700, area=self.downtown, sleep="early")
        self.client.login(username="viewer@example.com", password=PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertEqual(self.names(response), ["close", "far"])
        scores = [p.score for p in response.context["profiles"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_logged_in_results_are_paginated(self):
        for i in range(12):
            make_student(f"s{i:02d}")
        self.client.login(username="viewer@example.com", password=PASSWORD)
        page1 = self.client.get(reverse("home"))
        page2 = self.client.get(reverse("home"), {"page": 2})
        self.assertEqual(len(page1.context["profiles"]), 9)
        self.assertEqual(len(page2.context["profiles"]), 3)


@FAST
class ProfileDetailTests(TestCase):
    def setUp(self):
        self.me, self.my_profile = make_student("viewer")
        self.other, self.other_profile = make_student("other", bio="Loves cooking")

    def url(self, profile):
        return reverse("profile_detail", args=[profile.pk])

    def test_missing_profile_returns_404(self):
        self.assertEqual(self.client.get(reverse("profile_detail", args=[9999])).status_code, 404)

    def test_guest_sees_limited_details(self):
        response = self.client.get(self.url(self.other_profile))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Loves cooking")
        self.assertNotContains(response, "Sleep schedule")

    def test_logged_in_user_sees_full_profile_and_score(self):
        self.client.login(username="viewer@example.com", password=PASSWORD)
        response = self.client.get(self.url(self.other_profile))
        self.assertContains(response, "Loves cooking")
        self.assertContains(response, "Sleep schedule")
        self.assertIsNotNone(response.context["score"])

    def test_own_profile_flag(self):
        self.client.login(username="viewer@example.com", password=PASSWORD)
        response = self.client.get(self.url(self.my_profile))
        self.assertTrue(response.context["is_own_profile"])

    def test_contact_details_hidden_until_request_accepted(self):
        self.client.login(username="viewer@example.com", password=PASSWORD)
        req = RoommateRequest.objects.create(sender=self.me, receiver=self.other)
        self.assertNotContains(self.client.get(self.url(self.other_profile)), "other@example.com")
        req.status = "accepted"
        req.save()
        self.assertContains(self.client.get(self.url(self.other_profile)), "other@example.com")


@FAST
class ShortlistTests(TestCase):
    def setUp(self):
        self.me, self.my_profile = make_student("viewer")
        self.other, self.other_profile = make_student("other")
        self.client.login(username="viewer@example.com", password=PASSWORD)

    def test_save_profile(self):
        self.client.post(reverse("save_profile", args=[self.other_profile.pk]))
        self.assertTrue(SavedProfile.objects.filter(user=self.me, profile=self.other_profile).exists())

    def test_saving_twice_keeps_one_entry(self):
        for _ in range(2):
            self.client.post(reverse("save_profile", args=[self.other_profile.pk]))
        self.assertEqual(SavedProfile.objects.filter(user=self.me).count(), 1)

    def test_cannot_save_own_profile(self):
        self.client.post(reverse("save_profile", args=[self.my_profile.pk]))
        self.assertEqual(SavedProfile.objects.count(), 0)

    def test_shortlist_lists_and_removes(self):
        self.client.post(reverse("save_profile", args=[self.other_profile.pk]))
        self.assertContains(self.client.get(reverse("saved_list")), "Other")
        self.client.post(reverse("unsave_profile", args=[self.other_profile.pk]))
        self.assertEqual(SavedProfile.objects.count(), 0)
        self.assertContains(self.client.get(reverse("saved_list")), "Your shortlist is empty")

    def test_save_requires_login_and_post(self):
        self.client.logout()
        response = self.client.post(reverse("save_profile", args=[self.other_profile.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])
        self.client.login(username="viewer@example.com", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("save_profile", args=[self.other_profile.pk])).status_code, 405)

    def test_open_redirect_is_blocked(self):
        response = self.client.post(
            reverse("save_profile", args=[self.other_profile.pk]), {"next": "http://evil.example/"}
        )
        self.assertTrue(response["Location"].startswith("/profile/"))
