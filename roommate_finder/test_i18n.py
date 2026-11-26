"""Tests for the English / French switch and for the new staff panel features."""
import importlib.util
from pathlib import Path

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from accounts.models import VerificationDocument
from matches.models import ContactMessage, RoommateRequest
from profiles.models import Profile
from profiles.tests import make_student

from django.contrib.auth import get_user_model

User = get_user_model()
PASSWORD = "Pass12345!"
FAST = override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
ROOT = Path(__file__).resolve().parent.parent


def load_builder():
    spec = importlib.util.spec_from_file_location("build_locale", ROOT / "locale" / "build_locale.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LanguageSwitchTests(TestCase):
    def test_default_is_english(self):
        html = self.client.get(reverse("home")).content.decode()
        self.assertIn('<html lang="en"', html)
        self.assertIn("Login", html)

    def test_switch_to_french_and_back(self):
        response = self.client.post(reverse("set_language"), {"language": "fr", "next": "/"})
        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertEqual(self.client.cookies["django_language"].value, "fr")
        html = self.client.get(reverse("home")).content.decode()
        self.assertIn('<html lang="fr"', html)
        self.assertIn("Connexion", html)
        self.assertIn("Accueil", html)
        self.client.post(reverse("set_language"), {"language": "en", "next": "/"})
        self.assertIn("Login", self.client.get(reverse("home")).content.decode())

    def test_browser_language_header_is_respected(self):
        html = self.client.get(reverse("home"), HTTP_ACCEPT_LANGUAGE="fr-CA,fr;q=0.9").content.decode()
        self.assertIn('<html lang="fr"', html)

    def test_unknown_language_is_ignored(self):
        self.client.post(reverse("set_language"), {"language": "xx", "next": "/"})
        self.assertIn('<html lang="en"', self.client.get(reverse("home")).content.decode())

    def test_switcher_button_on_site_and_panel(self):
        self.assertContains(self.client.get(reverse("home")), 'name="language" value="fr"')
        User.objects.create_user("staff@example.com", PASSWORD, is_staff=True)
        self.client.login(username="staff@example.com", password=PASSWORD)
        self.assertContains(self.client.get(reverse("panel:dashboard")), 'name="language" value="fr"')
        self.client.post(reverse("set_language"), {"language": "fr", "next": "/"})
        self.assertContains(self.client.get(reverse("panel:dashboard")), 'name="language" value="en"')

    def test_open_redirect_is_blocked(self):
        response = self.client.post(reverse("set_language"), {"language": "fr", "next": "https://evil.example/"})
        self.assertEqual(response["Location"], "/")


class CatalogTests(TestCase):
    def test_every_text_in_the_code_has_a_french_translation(self):
        builder = load_builder()
        found = {**builder.extract_templates(), **builder.extract_python()}
        missing = [m for m in found if m not in builder.FR]
        self.assertEqual(missing, [], "Add these to locale/fr_translations.py and run locale/build_locale.py")

    def test_compiled_catalog_matches_the_translations_file(self):
        builder = load_builder()
        with translation.override("fr"):
            for msgid, french in builder.FR.items():
                if isinstance(french, tuple) or msgid in builder.DYNAMIC:
                    continue
                self.assertEqual(translation.gettext(msgid), french, msgid)

    def test_plural_forms(self):
        with translation.override("fr"):
            self.assertEqual(translation.ngettext("%(n)d record updated.", "%(n)d records updated.", 1) % {"n": 1},
                             "1 enregistrement mis à jour.")
            self.assertEqual(translation.ngettext("%(n)d record updated.", "%(n)d records updated.", 3) % {"n": 3},
                             "3 enregistrements mis à jour.")

    def test_placeholders_match_between_english_and_french(self):
        builder = load_builder()
        for msgid, french in builder.FR.items():
            if isinstance(french, tuple):
                continue
            self.assertEqual(builder.placeholders(msgid), builder.placeholders(french), msgid)


@FAST
class FrenchPagesTests(TestCase):
    def setUp(self):
        self.me, self.mine = make_student("viewer")
        self.other_user, self.other = make_student("other")
        self.client.login(username="viewer@example.com", password=PASSWORD)
        self.client.post(reverse("set_language"), {"language": "fr", "next": "/"})

    def test_home_in_french(self):
        html = self.client.get(reverse("home")).content.decode()
        self.assertIn("Meilleure compatibilité", html)
        self.assertIn("de compatibilité", html)
        self.assertIn("Voir le profil", html)

    def test_profile_page_in_french(self):
        html = self.client.get(reverse("profile_detail", args=[self.other.pk])).content.decode()
        self.assertIn("Pourquoi vous êtes compatibles", html)
        self.assertIn("Horaire de sommeil", html)
        self.assertIn("Envoyer une demande de colocation", html)

    def test_forms_are_in_french(self):
        html = self.client.get(reverse("profile_edit")).content.decode()
        self.assertIn("Nom complet", html)
        self.assertIn("Secteur préféré", html)
        self.assertIn("Lève-tôt", html)

    def test_flash_message_in_french(self):
        response = self.client.post(reverse("send_request", args=[self.other.pk]), {"message": "Salut"}, follow=True)
        self.assertContains(response, "Demande de colocation envoyée.")

    def test_request_email_is_in_french(self):
        self.client.post(reverse("send_request", args=[self.other.pk]), {"message": "Salut"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Nouvelle demande de colocation", mail.outbox[0].subject)
        self.assertIn("Bonjour", mail.outbox[0].body)

    def test_status_labels_in_french(self):
        RoommateRequest.objects.create(sender=self.me, receiver=self.other_user)
        self.assertContains(self.client.get(reverse("request_inbox")), "En attente")

    def test_login_error_in_french(self):
        self.client.logout()  # logging out also clears the test client's cookies
        self.client.post(reverse("set_language"), {"language": "fr", "next": "/"})
        response = self.client.post(reverse("login"), {"username": "nobody@example.com", "password": "x"})
        self.assertContains(response, "adresse e-mail")

    def test_password_reset_email_in_french(self):
        self.client.logout()
        self.client.post(reverse("set_language"), {"language": "fr", "next": "/"})
        self.client.post(reverse("password_reset"), {"email": "viewer@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Réinitialisez votre mot de passe", mail.outbox[0].subject)
        self.assertIn("Choisissez un nouveau mot de passe", mail.outbox[0].body)

    def test_dates_use_french_format(self):
        html = self.client.get(reverse("history")).content.decode()
        self.assertIn("Dernière visite", html)

    def test_english_still_works_for_other_visitors(self):
        other_client = self.client_class()
        self.assertIn("Login", other_client.get(reverse("home")).content.decode())


@FAST
class PanelFrenchTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user("staff@example.com", PASSWORD, is_staff=True)
        self.client.login(username="staff@example.com", password=PASSWORD)
        self.client.post(reverse("set_language"), {"language": "fr", "next": "/"})

    def test_dashboard_in_french(self):
        html = self.client.get(reverse("panel:dashboard")).content.decode()
        for text in ("Aperçu", "Demande votre attention", "Activité récente", "Pages vues, 14 derniers jours"):
            self.assertIn(text, html)

    def test_sidebar_and_headers_in_french(self):
        html = self.client.get(reverse("panel:list", args=["users"])).content.decode()
        self.assertIn("Utilisateurs", html)
        self.assertIn("Adresse e-mail", html)
        self.assertIn("Ajouter un utilisateur", html)

    def test_profile_columns_in_french(self):
        make_student("aisha")
        html = self.client.get(reverse("panel:list", args=["profiles"])).content.decode()
        self.assertIn("Nom complet", html)
        self.assertIn("Secteur préféré", html)

    def test_form_labels_in_french(self):
        html = self.client.get(reverse("panel:create", args=["areas"])).content.decode()
        self.assertIn("Ajouter un secteur", html)
        self.assertIn("Description", html)

    def test_flash_messages_in_french(self):
        response = self.client.post(reverse("panel:create", args=["areas"]), {"name": "Centre", "description": ""}, follow=True)
        self.assertContains(response, "Enregistrement créé.")

    def test_confirm_delete_in_french(self):
        user, _ = make_student("zed")
        html = self.client.get(reverse("panel:delete", args=["users", user.pk])).content.decode()
        self.assertIn("Vous êtes sur le point de supprimer", html)


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
