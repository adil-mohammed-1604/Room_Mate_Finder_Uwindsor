from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import VerificationDocument
from matches.models import ContactMessage, RoommateRequest
from profiles.models import Area, Profile

User = get_user_model()


def make_profile(email, name):
    user = User.objects.create_user(email=email, password="Pass12345!")
    return user, Profile.objects.create(user=user, full_name=name, budget=700)


class PanelAccessTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(email="s@example.com", password="Pass12345!")
        self.staff = User.objects.create_user(email="staff@example.com", password="Pass12345!", is_staff=True)
        self.boss = User.objects.create_superuser(email="boss@example.com", password="Pass12345!")

    def test_guest_is_sent_to_login(self):
        response = self.client.get(reverse("panel:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_student_is_refused(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("panel:dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("panel:list", args=["users"])).status_code, 403)

    def test_staff_and_superuser_can_open_every_screen(self):
        from panel.registry import CONFIG
        for account in (self.staff, self.boss):
            self.client.force_login(account)
            self.assertEqual(self.client.get(reverse("panel:dashboard")).status_code, 200)
            for slug in CONFIG:
                self.assertEqual(self.client.get(reverse("panel:list", args=[slug])).status_code, 200, slug)

    def test_unknown_section_is_404(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get("/manage/nothing/").status_code, 404)

    def test_theme_colours_reach_the_page(self):
        self.client.force_login(self.staff)
        with self.settings(PANEL_THEME={"primary": "#123456", "brand_name": "My Admin"}):
            html = self.client.get(reverse("panel:dashboard")).content.decode()
        self.assertIn("--panel-primary:#123456", html)
        self.assertIn("My Admin", html)

    def test_admin_pages_use_the_theme_too(self):
        self.client.force_login(self.boss)
        html = self.client.get("/admin/").content.decode()
        self.assertIn("RoomMate Admin", html)


class PanelUsersTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@example.com", password="Pass12345!", is_staff=True)
        self.boss = User.objects.create_superuser(email="boss@example.com", password="Pass12345!")
        self.client.force_login(self.staff)

    def test_create_user_lowercases_email_and_sets_password(self):
        response = self.client.post(reverse("panel:create", args=["users"]), {
            "email": "New.Person@Example.com", "first_name": "New", "last_name": "Person",
            "is_active": "on", "password1": "Sup3rSecret!pw", "password2": "Sup3rSecret!pw",
        })
        self.assertRedirects(response, reverse("panel:list", args=["users"]))
        user = User.objects.get(email="new.person@example.com")
        self.assertTrue(user.check_password("Sup3rSecret!pw"))

    def test_create_user_needs_password_and_unique_email(self):
        response = self.client.post(reverse("panel:create", args=["users"]), {"email": "staff@EXAMPLE.com"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertContains(response, "Password is required")

    def test_staff_cannot_grant_superuser(self):
        target = User.objects.create_user(email="t@example.com", password="Pass12345!")
        self.client.post(reverse("panel:edit", args=["users", target.pk]), {
            "email": "t@example.com", "is_active": "on", "is_superuser": "on"})
        target.refresh_from_db()
        self.assertFalse(target.is_superuser)

    def test_staff_cannot_edit_or_delete_superuser(self):
        self.assertEqual(self.client.get(reverse("panel:edit", args=["users", self.boss.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("panel:delete", args=["users", self.boss.pk])).status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.boss.pk).exists())

    def test_cannot_delete_yourself(self):
        self.client.post(reverse("panel:delete", args=["users", self.staff.pk]))
        self.assertTrue(User.objects.filter(pk=self.staff.pk).exists())

    def test_edit_with_new_password(self):
        target = User.objects.create_user(email="t@example.com", password="Pass12345!")
        self.client.post(reverse("panel:edit", args=["users", target.pk]), {
            "email": "t@example.com", "is_active": "on",
            "password1": "An0ther!Pass99", "password2": "An0ther!Pass99"})
        target.refresh_from_db()
        self.assertTrue(target.check_password("An0ther!Pass99"))

    def test_delete_user_with_confirmation(self):
        target = User.objects.create_user(email="t@example.com", password="Pass12345!")
        self.assertEqual(self.client.get(reverse("panel:delete", args=["users", target.pk])).status_code, 200)
        self.client.post(reverse("panel:delete", args=["users", target.pk]))
        self.assertFalse(User.objects.filter(pk=target.pk).exists())

    def test_search_and_filter(self):
        User.objects.create_user(email="findme@example.com", password="Pass12345!")
        response = self.client.get(reverse("panel:list", args=["users"]), {"q": "findme"})
        self.assertContains(response, "findme@example.com")
        self.assertNotContains(response, "boss@example.com")
        response = self.client.get(reverse("panel:list", args=["users"]), {"is_staff": "0"})
        self.assertContains(response, "findme@example.com")
        self.assertEqual(response.context["page"].paginator.count, 1)  # staff and boss are filtered out


class PanelModerationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@example.com", password="Pass12345!", is_staff=True)
        self.client.force_login(self.staff)
        self.user, self.profile = make_profile("a@example.com", "Aisha")

    def make_doc(self):
        doc = VerificationDocument(profile=self.profile)
        doc.student_id.name = "student_ids/x.png"
        doc.save()
        return doc

    def test_approve_and_reject_update_verified_badge(self):
        doc = self.make_doc()
        self.client.post(reverse("panel:action", args=["verifications", doc.pk, "approve"]))
        doc.refresh_from_db(); self.profile.refresh_from_db()
        self.assertEqual(doc.status, "approved")
        self.assertIsNotNone(doc.reviewed_at)
        self.assertTrue(self.profile.is_verified)
        self.client.post(reverse("panel:action", args=["verifications", doc.pk, "reject"]))
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_verified)

    def test_actions_need_post(self):
        doc = self.make_doc()
        response = self.client.get(reverse("panel:action", args=["verifications", doc.pk, "approve"]))
        self.assertEqual(response.status_code, 405)

    def test_unknown_action_is_404(self):
        doc = self.make_doc()
        self.assertEqual(self.client.post(reverse("panel:action", args=["verifications", doc.pk, "boom"])).status_code, 404)

    def test_edit_verification_sets_review_time_and_badge(self):
        doc = self.make_doc()
        self.client.post(reverse("panel:edit", args=["verifications", doc.pk]),
                         {"status": "approved", "admin_notes": "looks good"})
        doc.refresh_from_db(); self.profile.refresh_from_db()
        self.assertEqual(doc.admin_notes, "looks good")
        self.assertIsNotNone(doc.reviewed_at)
        self.assertTrue(self.profile.is_verified)

    def test_deleting_approved_document_removes_badge(self):
        doc = self.make_doc()
        self.client.post(reverse("panel:action", args=["verifications", doc.pk, "approve"]))
        self.client.post(reverse("panel:delete", args=["verifications", doc.pk]))
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_verified)

    def test_verification_list_has_view_approve_reject_buttons(self):
        self.make_doc()
        html = self.client.get(reverse("panel:list", args=["verifications"])).content.decode()
        for word in ("View ID", "Approve", "Reject"):
            self.assertIn(word, html)

    def test_resolve_and_reopen_message(self):
        msg = ContactMessage.objects.create(name="N", email="n@example.com", subject="Hi", message="Hello there friend")
        self.client.post(reverse("panel:action", args=["messages", msg.pk, "resolve"]))
        msg.refresh_from_db(); self.assertTrue(msg.is_resolved)
        self.client.post(reverse("panel:action", args=["messages", msg.pk, "reopen"]))
        msg.refresh_from_db(); self.assertFalse(msg.is_resolved)

    def test_message_edit_page_shows_details(self):
        msg = ContactMessage.objects.create(name="Nina", email="n@example.com", subject="Help", message="Hello there friend")
        self.assertContains(self.client.get(reverse("panel:edit", args=["messages", msg.pk])), "Hello there friend")

    def test_request_status_change_sets_responded_at(self):
        _, other = make_profile("b@example.com", "Brian")
        req = RoommateRequest.objects.create(sender=self.user, receiver=other.user)
        self.client.post(reverse("panel:edit", args=["requests", req.pk]), {"status": "declined"})
        req.refresh_from_db()
        self.assertEqual(req.status, "declined")
        self.assertIsNotNone(req.responded_at)

    def test_reactivating_duplicate_request_shows_error_not_crash(self):
        _, other = make_profile("b@example.com", "Brian")
        old = RoommateRequest.objects.create(sender=self.user, receiver=other.user, status="declined")
        RoommateRequest.objects.create(sender=self.user, receiver=other.user, status="pending")
        response = self.client.post(reverse("panel:edit", args=["requests", old.pk]), {"status": "pending"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "duplicate")

    def test_safe_next_blocks_outside_redirects(self):
        doc = self.make_doc()
        response = self.client.post(reverse("panel:action", args=["verifications", doc.pk, "approve"]),
                                    {"next": "https://evil.example/"})
        self.assertEqual(response["Location"], reverse("panel:list", args=["verifications"]))


class PanelCrudTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@example.com", password="Pass12345!", is_staff=True)
        self.client.force_login(self.staff)

    def test_area_create_edit_delete(self):
        self.client.post(reverse("panel:create", args=["areas"]), {"name": "Sandwich", "description": "West"})
        area = Area.objects.get(name="Sandwich")
        self.client.post(reverse("panel:edit", args=["areas", area.pk]), {"name": "Sandwich Town", "description": ""})
        area.refresh_from_db(); self.assertEqual(area.name, "Sandwich Town")
        self.client.post(reverse("panel:delete", args=["areas", area.pk]))
        self.assertFalse(Area.objects.filter(pk=area.pk).exists())

    def test_profile_edit_toggles_verified(self):
        user, profile = make_profile("a@example.com", "Aisha")
        self.client.post(reverse("panel:edit", args=["profiles", profile.pk]), {
            "user": user.pk, "full_name": "Aisha K", "budget": 900, "is_verified": "on"})
        profile.refresh_from_db()
        self.assertEqual(profile.full_name, "Aisha K")
        self.assertTrue(profile.is_verified)

    def test_read_only_sections_have_no_add_or_edit(self):
        self.assertEqual(self.client.get(reverse("panel:create", args=["visits"])).status_code, 404)
        self.assertEqual(self.client.get(reverse("panel:create", args=["verifications"])).status_code, 404)
        user, profile = make_profile("a@example.com", "Aisha")
        from profiles.models import SavedProfile
        saved = SavedProfile.objects.create(user=user, profile=profile)
        self.assertEqual(self.client.get(reverse("panel:edit", args=["saved", saved.pk])).status_code, 404)

    def test_dashboard_numbers(self):
        make_profile("a@example.com", "Aisha")
        html = self.client.get(reverse("panel:dashboard")).content.decode()
        self.assertIn("Pending IDs", html)
        self.assertIn("Page views", html)

    def test_pagination(self):
        for i in range(20):
            User.objects.create_user(email=f"u{i}@example.com", password="Pass12345!")
        response = self.client.get(reverse("panel:list", args=["users"]), {"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Page 2 of 2")
