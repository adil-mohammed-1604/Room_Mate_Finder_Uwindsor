"""Tests for the staff panel workflow (tabs, sorting, bulk actions, dashboard, theme)."""
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import VerificationDocument
from matches.models import ContactMessage, RoommateRequest
from profiles.models import Profile
from profiles.tests import make_student

from django.contrib.auth import get_user_model

User = get_user_model()
PASSWORD = "Pass12345!"
FAST = override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])


@FAST
class PanelWorkflowTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff@example.com", PASSWORD, is_staff=True)
        self.boss = User.objects.create_superuser("boss@example.com", PASSWORD)
        self.client.login(username="staff@example.com", password=PASSWORD)
        self.u1, self.p1 = make_student("aisha")
        self.u2, self.p2 = make_student("brian")

    def doc(self, profile, status="pending"):
        d = VerificationDocument(profile=profile, status=status)
        d.student_id.name = "student_ids/x.png"
        d.save()
        return d

    def test_status_tabs_filter_and_count(self):
        self.doc(self.p1, "pending")
        self.doc(self.p2, "approved")
        response = self.client.get(reverse("panel:list", args=["verifications"]), {"status": "pending"})
        self.assertEqual(response.context["page"].paginator.count, 1)
        tabs = {t["label"]: t["count"] for t in response.context["tabs"]}
        self.assertEqual(tabs["Pending"], 1)
        self.assertEqual(tabs["Approved"], 1)
        self.assertEqual(tabs["All"], 2)

    def test_message_tabs(self):
        ContactMessage.objects.create(name="A", email="a@example.com", subject="One", message="long enough text", is_resolved=True)
        ContactMessage.objects.create(name="B", email="b@example.com", subject="Two", message="long enough text")
        response = self.client.get(reverse("panel:list", args=["messages"]), {"is_resolved": "0"})
        self.assertEqual([r["obj"].subject for r in response.context["rows"]], ["Two"])

    def test_sorting_by_column(self):
        asc = self.client.get(reverse("panel:list", args=["users"]), {"o": "email"})
        desc = self.client.get(reverse("panel:list", args=["users"]), {"o": "-email"})
        emails = [r["obj"].email for r in asc.context["rows"]]
        self.assertEqual(emails, sorted(emails))
        self.assertEqual([r["obj"].email for r in desc.context["rows"]], sorted(emails, reverse=True))

    def test_bad_sort_value_is_ignored(self):
        self.assertEqual(self.client.get(reverse("panel:list", args=["users"]), {"o": "password; drop"}).status_code, 200)

    def test_bulk_approve_and_reject(self):
        d1, d2 = self.doc(self.p1), self.doc(self.p2)
        self.client.post(reverse("panel:bulk", args=["verifications"]), {"action": "approve", "ids": [d1.pk, d2.pk]})
        self.p1.refresh_from_db(); self.p2.refresh_from_db()
        self.assertTrue(self.p1.is_verified and self.p2.is_verified)
        self.client.post(reverse("panel:bulk", args=["verifications"]), {"action": "reject", "ids": [d1.pk]})
        self.p1.refresh_from_db()
        self.assertFalse(self.p1.is_verified)

    def test_bulk_resolve_and_reopen(self):
        m = [ContactMessage.objects.create(name="A", email="a@example.com", subject=str(i), message="long enough text")
             for i in range(2)]
        self.client.post(reverse("panel:bulk", args=["messages"]), {"action": "resolve", "ids": [x.pk for x in m]})
        self.assertEqual(ContactMessage.objects.filter(is_resolved=True).count(), 2)
        self.client.post(reverse("panel:bulk", args=["messages"]), {"action": "reopen", "ids": [m[0].pk]})
        self.assertEqual(ContactMessage.objects.filter(is_resolved=True).count(), 1)

    def test_bulk_delete_updates_verified_badge(self):
        d = self.doc(self.p1, "approved")
        self.p1.is_verified = True; self.p1.save()
        self.client.post(reverse("panel:bulk", args=["verifications"]), {"action": "delete", "ids": [d.pk]})
        self.p1.refresh_from_db()
        self.assertFalse(self.p1.is_verified)

    def test_bulk_delete_users_protects_self_and_superusers(self):
        response = self.client.post(reverse("panel:bulk", args=["users"]), {
            "action": "delete", "ids": [self.staff.pk, self.boss.pk, self.u1.pk]}, follow=True)
        self.assertTrue(User.objects.filter(pk=self.staff.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.boss.pk).exists())
        self.assertFalse(User.objects.filter(pk=self.u1.pk).exists())
        self.assertContains(response, "skipped")

    def test_bulk_needs_post_and_known_action(self):
        self.assertEqual(self.client.get(reverse("panel:bulk", args=["users"])).status_code, 405)
        self.assertEqual(self.client.post(reverse("panel:bulk", args=["users"]), {"action": "approve", "ids": [1]}).status_code, 404)
        self.assertEqual(self.client.post(reverse("panel:bulk", args=["areas"]), {"action": "resolve", "ids": [1]}).status_code, 404)

    def test_bulk_with_nothing_ticked(self):
        response = self.client.post(reverse("panel:bulk", args=["users"]), {"action": "delete"}, follow=True)
        self.assertContains(response, "Tick at least one row first.")

    def test_bulk_requires_staff(self):
        self.client.logout()
        self.client.login(username="aisha@example.com", password=PASSWORD)
        self.assertEqual(self.client.post(reverse("panel:bulk", args=["users"]), {"action": "delete", "ids": [self.u2.pk]}).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.u2.pk).exists())

    def test_dashboard_with_data(self):
        RoommateRequest.objects.create(sender=self.u1, receiver=self.u2, status="accepted")
        RoommateRequest.objects.create(sender=self.u2, receiver=self.u1, status="declined")
        ContactMessage.objects.create(name="A", email="a@example.com", subject="Help", message="long enough text")
        self.doc(self.p1)
        response = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "conic-gradient(")
        self.assertContains(response, "Recent activity")
        self.assertContains(response, "uploaded a student ID")
        self.assertEqual(response.context["request_total"], 2)

    def test_dashboard_empty_state(self):
        User.objects.exclude(pk=self.staff.pk).delete()
        self.assertEqual(self.client.get(reverse("panel:dashboard")).status_code, 200)

    def test_panel_dark_mode_toggle(self):
        self.assertContains(self.client.get(reverse("panel:dashboard")), 'id="themeToggle"')
        self.client.cookies["theme"] = "dark"
        self.assertContains(self.client.get(reverse("panel:dashboard")), 'data-bs-theme="dark"')

    def test_theme_settings_still_apply(self):
        with self.settings(PANEL_THEME={"primary": "#123456"}):
            html = self.client.get(reverse("panel:dashboard")).content.decode()
        self.assertIn("--panel-primary:#123456", html)
        self.assertLess(html.index("panel/panel.css"), html.index("--panel-primary:#123456"))

    def test_avatars_and_badges(self):
        self.doc(self.p1)
        self.assertContains(self.client.get(reverse("panel:list", args=["users"])), "panel-avatar")
        self.assertContains(self.client.get(reverse("panel:list", args=["verifications"])), "text-bg-warning")

    def test_list_has_bulk_toolbar_and_shortcuts(self):
        html = self.client.get(reverse("panel:list", args=["verifications"])).content.decode()
        self.assertIn('id="bulkBar"', html)
        self.assertIn('data-shortcut="add"', self.client.get(reverse("panel:list", args=["areas"])).content.decode())
