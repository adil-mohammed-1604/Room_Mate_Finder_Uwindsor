# Owner: Nazim Ali Firdous
"""Tests for accounts: sign-up, login, profile CRUD, uploads, ID verification, password reset."""
import io
import os
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from profiles.models import Area, Profile

from .models import LifestylePreference, VerificationDocument, validate_id_file

User = get_user_model()
PASSWORD = "Pass12345!"
# Fast password hashing so the tests run in seconds (tests only, not the real site)
FAST = override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])


def make_png(name="photo.png", fmt="PNG", extra_kb=0):
    buf = io.BytesIO()
    Image.new("RGB", (30, 30), "green").save(buf, fmt)
    data = buf.getvalue() + b"0" * (extra_kb * 1024)
    return SimpleUploadedFile(name, data, content_type="image/png")


def make_user(username="nazim", with_profile=True, **profile_kwargs):
    user = User.objects.create_user(f"{username}@example.com", PASSWORD)
    profile = None
    if with_profile:
        profile = Profile.objects.create(
            user=user, full_name=username.title(), budget=700, **profile_kwargs
        )
        LifestylePreference.objects.create(profile=profile)
    return user, profile


PROFILE_DATA = {
    "full_name": "New Student", "program": "Biology", "bio": "Hello", "phone": "",
    "budget": 650, "sleep_schedule": "early", "cleanliness": 4, "pets": "ok",
    "smoking": "no", "guests_often": "no",
}


class TempFilesMixin:
    """Send uploaded photos and student IDs to a temporary folder, then delete it."""

    def setUp(self):
        super().setUp()
        self._tmp = tempfile.mkdtemp()
        self._override = override_settings(MEDIA_ROOT=self._tmp)
        self._override.enable()
        self._field = VerificationDocument._meta.get_field("student_id")
        self._old_storage = self._field.storage
        self._field.storage = FileSystemStorage(location=self._tmp)

    def tearDown(self):
        self._field.storage = self._old_storage
        self._override.disable()
        shutil.rmtree(self._tmp, ignore_errors=True)
        super().tearDown()


@FAST
class SignUpTests(TestCase):
    data = {"email": "new@example.com",
            "password1": "Sup3r-secret-pw", "password2": "Sup3r-secret-pw"}

    def test_signup_page_asks_for_email_not_username(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="email"')
        self.assertNotContains(response, 'name="username"')

    def test_valid_signup_creates_user_logs_in_and_goes_to_profile_form(self):
        response = self.client.post(reverse("signup"), self.data)
        self.assertRedirects(response, reverse("profile_create"))
        self.assertTrue(User.objects.filter(email="new@example.com").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_email_is_saved_in_lowercase(self):
        self.client.post(reverse("signup"), {**self.data, "email": "New@Example.COM"})
        self.assertEqual(User.objects.get().email, "new@example.com")

    def test_duplicate_email_rejected_case_insensitive(self):
        make_user("someone", with_profile=False)
        response = self.client.post(
            reverse("signup"), {**self.data, "email": "SOMEONE@example.com"}
        )
        self.assertContains(response, "already exists")
        self.assertEqual(User.objects.count(), 1)

    def test_password_mismatch_rejected(self):
        response = self.client.post(reverse("signup"), {**self.data, "password2": "different-pw-1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_weak_password_rejected(self):
        response = self.client.post(
            reverse("signup"), {**self.data, "password1": "12345678", "password2": "12345678"}
        )
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_missing_or_invalid_email_rejected(self):
        for bad in ("", "not-an-email", "a@b"):
            response = self.client.post(reverse("signup"), {**self.data, "email": bad})
            self.assertEqual(response.status_code, 200, bad)
        self.assertEqual(User.objects.count(), 0)

    def test_logged_in_user_is_sent_away_from_signup(self):
        make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)
        self.assertRedirects(self.client.get(reverse("signup")), reverse("home"))


@FAST
class LoginTests(TestCase):
    """Students log in with their email address."""

    def setUp(self):
        make_user("nazim")  # email: nazim@example.com

    def login(self, email, password=PASSWORD, **extra):
        return self.client.post(reverse("login"), {"username": email, "password": password, **extra})

    def test_login_page_asks_for_email(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, 'type="email"')
        self.assertContains(response, ">Email</label>")

    def test_login_with_email_redirects_home(self):
        self.assertRedirects(self.login("nazim@example.com"), reverse("home"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_email_login_ignores_case_and_spaces(self):
        self.login("  Nazim@Example.COM ")
        self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_shows_error_and_does_not_log_in(self):
        response = self.login("nazim@example.com", "wrong")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "correct email and password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_email_cannot_log_in(self):
        response = self.login("ghost@example.com")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 200)

    def test_login_follows_next(self):
        response = self.login("nazim@example.com", next="/matches/requests/")
        self.assertRedirects(response, "/matches/requests/", fetch_redirect_response=False)

    def test_inactive_user_cannot_log_in(self):
        User.objects.filter(email="nazim@example.com").update(is_active=False)
        self.login("nazim@example.com")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post_and_logs_out(self):
        self.client.login(username="nazim@example.com", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_reset_email_greets_by_name_or_email(self):
        self.client.post(reverse("password_reset"), {"email": "nazim@example.com"})
        self.assertIn("Hi Nazim,", mail.outbox[0].body)  # profile full name
        mail.outbox.clear()
        make_user("noprofile", with_profile=False)
        self.client.post(reverse("password_reset"), {"email": "noprofile@example.com"})
        self.assertIn("Hi noprofile@example.com,", mail.outbox[0].body)  # email fallback


@FAST
class UserModelTests(TestCase):
    """The custom user model: the email is the login and there is no username."""

    def test_there_is_no_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertNotIn("username", [f.name for f in User._meta.get_fields()])

    def test_create_user_normalizes_email_and_hashes_password(self):
        user = User.objects.create_user("  Sam@Example.COM ", PASSWORD)
        self.assertEqual(user.email, "sam@example.com")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_str_and_get_username_are_the_email(self):
        user = User.objects.create_user("sam@example.com", PASSWORD)
        self.assertEqual(str(user), "sam@example.com")
        self.assertEqual(user.get_username(), "sam@example.com")

    def test_email_is_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", PASSWORD)

    def test_duplicate_email_is_blocked_by_the_database(self):
        User.objects.create_user("sam@example.com", PASSWORD)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user("SAM@example.com", PASSWORD)

    def test_natural_key_lookup_ignores_case(self):
        user = User.objects.create_user("sam@example.com", PASSWORD)
        self.assertEqual(User.objects.get_by_natural_key("SAM@Example.com"), user)

    def test_create_superuser_sets_flags(self):
        boss = User.objects.create_superuser("boss@example.com", PASSWORD)
        self.assertTrue(boss.is_staff and boss.is_superuser)
        with self.assertRaises(ValueError):
            User.objects.create_superuser("x@example.com", PASSWORD, is_staff=False)

    def test_createsuperuser_command_asks_for_email(self):
        with mock.patch.dict(os.environ, {"DJANGO_SUPERUSER_PASSWORD": "Admin12345!"}):
            call_command("createsuperuser", interactive=False, email="root@example.com", verbosity=0)
        root = User.objects.get(email="root@example.com")
        self.assertTrue(root.is_superuser and root.check_password("Admin12345!"))


@FAST
class AdminUserTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_superuser("boss@example.com", PASSWORD)
        self.client.login(username="boss@example.com", password=PASSWORD)

    def test_admin_login_uses_email(self):
        self.client.logout()
        response = self.client.post(
            "/admin/login/", {"username": "boss@example.com", "password": PASSWORD, "next": "/admin/"}
        )
        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)

    def test_students_cannot_use_the_admin(self):
        make_user("nazim", with_profile=False)
        self.client.logout()
        response = self.client.post(
            "/admin/login/", {"username": "nazim@example.com", "password": PASSWORD, "next": "/admin/"}
        )
        self.assertEqual(response.status_code, 200)

    def test_user_list_search_and_change_pages_load(self):
        make_user("nazim", with_profile=False)
        self.assertContains(self.client.get("/admin/accounts/user/?q=nazim"), "nazim@example.com")
        change = f"/admin/accounts/user/{self.boss.pk}/change/"
        self.assertEqual(self.client.get(change).status_code, 200)

    def test_admin_can_add_a_user_with_email_and_password(self):
        response = self.client.post(
            "/admin/accounts/user/add/",
            {"email": "added@example.com", "password1": "Sup3r-secret-pw", "password2": "Sup3r-secret-pw"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.get(email="added@example.com").check_password("Sup3r-secret-pw"))


@FAST
class ProfileCrudTests(TempFilesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.area = Area.objects.create(name="Downtown")

    def test_pages_require_login(self):
        for name in ("profile_create", "profile_edit", "profile_delete"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertIn("login", response["Location"])

    def test_create_profile_saves_profile_and_lifestyle(self):
        make_user("fresh", with_profile=False)
        self.client.login(username="fresh@example.com", password=PASSWORD)
        response = self.client.post(reverse("profile_create"), PROFILE_DATA)
        profile = Profile.objects.get(user__email="fresh@example.com")
        self.assertRedirects(response, reverse("profile_detail", args=[profile.pk]))
        self.assertEqual(profile.lifestyle.sleep_schedule, "early")

    def test_create_twice_redirects_to_edit(self):
        make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)
        self.assertRedirects(self.client.get(reverse("profile_create")), reverse("profile_edit"))

    def test_edit_without_profile_redirects_to_create(self):
        make_user("fresh", with_profile=False)
        self.client.login(username="fresh@example.com", password=PASSWORD)
        self.assertRedirects(self.client.get(reverse("profile_edit")), reverse("profile_create"))

    def test_invalid_budget_rejected(self):
        make_user("fresh", with_profile=False)
        self.client.login(username="fresh@example.com", password=PASSWORD)
        for bad in ("0", "-5", "abc", ""):
            response = self.client.post(reverse("profile_create"), {**PROFILE_DATA, "budget": bad})
            self.assertEqual(response.status_code, 200, bad)
        self.assertFalse(Profile.objects.filter(user__email="fresh@example.com").exists())

    def test_missing_required_fields_rejected(self):
        make_user("fresh", with_profile=False)
        self.client.login(username="fresh@example.com", password=PASSWORD)
        response = self.client.post(reverse("profile_create"), {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.filter(user__email="fresh@example.com").exists())

    def test_edit_updates_profile(self):
        _, profile = make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)
        self.client.post(reverse("profile_edit"), {**PROFILE_DATA, "full_name": "Changed Name"})
        profile.refresh_from_db()
        self.assertEqual(profile.full_name, "Changed Name")

    def test_delete_needs_post_and_keeps_account(self):
        user, profile = make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("profile_delete")).status_code, 200)
        self.assertTrue(Profile.objects.filter(pk=profile.pk).exists())
        self.client.post(reverse("profile_delete"))
        self.assertFalse(Profile.objects.filter(pk=profile.pk).exists())
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_png_photo_accepted(self):
        _, profile = make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)
        response = self.client.post(reverse("profile_edit"), {**PROFILE_DATA, "photo": make_png()})
        self.assertEqual(response.status_code, 302)
        profile.refresh_from_db()
        self.assertTrue(profile.photo.name.startswith("profile_photos/"))

    def test_gif_photo_rejected(self):
        _, profile = make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)
        response = self.client.post(
            reverse("profile_edit"), {**PROFILE_DATA, "photo": make_png("x.gif", "GIF")}
        )
        self.assertContains(response, "JPG or PNG")
        profile.refresh_from_db()
        self.assertFalse(profile.photo)

    def test_oversized_photo_rejected(self):
        _, profile = make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)
        response = self.client.post(
            reverse("profile_edit"), {**PROFILE_DATA, "photo": make_png(extra_kb=2100)}
        )
        self.assertContains(response, "too large")

    def test_fake_image_rejected(self):
        make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)
        fake = SimpleUploadedFile("evil.png", b"not really an image", content_type="image/png")
        response = self.client.post(reverse("profile_edit"), {**PROFILE_DATA, "photo": fake})
        self.assertEqual(response.status_code, 200)


@FAST
class VerificationTests(TempFilesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user, self.profile = make_user("nazim")
        self.client.login(username="nazim@example.com", password=PASSWORD)

    def upload(self, file):
        return self.client.post(reverse("verify_upload"), {"student_id": file})

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("verify_upload")).status_code, 302)

    def test_user_without_profile_is_sent_to_create_profile(self):
        make_user("fresh", with_profile=False)
        self.client.login(username="fresh@example.com", password=PASSWORD)
        self.assertRedirects(self.client.get(reverse("verify_upload")), reverse("profile_create"))

    def test_upload_creates_pending_document(self):
        response = self.upload(make_png("id.png"))
        self.assertRedirects(response, reverse("profile_detail", args=[self.profile.pk]))
        doc = VerificationDocument.objects.get(profile=self.profile)
        self.assertEqual(doc.status, "pending")
        self.assertFalse(self.profile.is_verified)

    def test_wrong_file_type_rejected(self):
        response = self.upload(SimpleUploadedFile("id.txt", b"hello", content_type="text/plain"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(VerificationDocument.objects.count(), 0)

    def test_oversized_file_rejected(self):
        response = self.upload(make_png("big.png", extra_kb=5200))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(VerificationDocument.objects.count(), 0)

    def test_pdf_is_allowed(self):
        self.upload(SimpleUploadedFile("id.pdf", b"%PDF-1.4 test", content_type="application/pdf"))
        self.assertEqual(VerificationDocument.objects.count(), 1)

    def test_second_upload_blocked_while_pending(self):
        self.upload(make_png("id.png"))
        self.upload(make_png("id2.png"))
        self.assertEqual(VerificationDocument.objects.count(), 1)

    def test_already_verified_user_is_redirected(self):
        self.profile.is_verified = True
        self.profile.save()
        response = self.client.get(reverse("verify_upload"))
        self.assertRedirects(response, reverse("profile_detail", args=[self.profile.pk]))

    def test_validate_id_file_rules(self):
        validate_id_file(SimpleUploadedFile("a.jpg", b"x"))
        with self.assertRaises(ValidationError):
            validate_id_file(SimpleUploadedFile("a.exe", b"x"))
        with self.assertRaises(ValidationError):
            validate_id_file(SimpleUploadedFile("a.png", b"x" * (5 * 1024 * 1024 + 1)))

    def test_student_id_is_not_publicly_served(self):
        self.upload(make_png("id.png"))
        doc = VerificationDocument.objects.get()
        self.assertEqual(self.client.get("/media/" + doc.student_id.name).status_code, 404)

    def test_only_staff_can_open_student_id(self):
        self.upload(make_png("id.png"))
        doc = VerificationDocument.objects.get()
        url = reverse("private_document", args=[doc.pk])
        self.assertEqual(self.client.get(url).status_code, 302)  # normal student
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)  # guest
        User.objects.create_superuser("boss@example.com", PASSWORD)
        self.client.login(username="boss@example.com", password=PASSWORD)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_admin_approve_and_reject_toggle_verified_badge(self):
        self.upload(make_png("id.png"))
        doc = VerificationDocument.objects.get()
        User.objects.create_superuser("boss@example.com", PASSWORD)
        self.client.login(username="boss@example.com", password=PASSWORD)
        url = reverse("admin:accounts_verificationdocument_changelist")
        self.client.post(url, {"action": "approve_documents", "_selected_action": [doc.pk]})
        self.profile.refresh_from_db()
        doc.refresh_from_db()
        self.assertTrue(self.profile.is_verified)
        self.assertEqual(doc.status, "approved")
        self.assertIsNotNone(doc.reviewed_at)
        self.client.post(url, {"action": "reject_documents", "_selected_action": [doc.pk]})
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.is_verified)


@FAST
class PasswordResetTests(TestCase):
    def setUp(self):
        make_user("nazim", with_profile=False)

    def test_reset_pages_load(self):
        self.assertEqual(self.client.get(reverse("password_reset")).status_code, 200)
        self.assertEqual(self.client.get(reverse("password_reset_done")).status_code, 200)

    def test_unknown_email_sends_nothing_but_looks_the_same(self):
        response = self.client.post(reverse("password_reset"), {"email": "nobody@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_known_email_sends_branded_email_with_working_link(self):
        response = self.client.post(reverse("password_reset"), {"email": "nazim@example.com"})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "Reset your RoomMate Finder password")
        self.assertIn("24 hours", message.body)
        self.assertEqual(len(message.alternatives), 1)
        link = [w for w in message.body.split() if "/reset/" in w][0]
        path = "/" + link.split("/", 3)[3]
        page = self.client.get(path, follow=True)
        self.assertContains(page, "Choose a new password")
        form_url = page.redirect_chain[-1][0]
        self.client.post(form_url, {"new_password1": "Brand-new-pass-77", "new_password2": "Brand-new-pass-77"})
        self.assertTrue(self.client.login(username="nazim@example.com", password="Brand-new-pass-77"))
        self.assertContains(self.client.get(path, follow=True), "Link no longer valid")
