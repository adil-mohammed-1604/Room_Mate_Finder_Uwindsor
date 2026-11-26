"""Copies the text that used to be hard-coded in about.html, team.html and faq.html into the database,
so the pages look the same until staff edit them in /manage/."""
from django.db import migrations

ABOUT_EN = (
    "Finding a good roommate is hard. Students search across Facebook groups, Kijiji posts and group chats "
    "with no way to compare people, and mismatched habits often lead to conflict.\n\n"
    "RoomMate Finder matches University of Windsor students on compatibility, not just rent: budget, area, "
    "sleep schedule, cleanliness and more. Verified students earn a badge after an admin checks their student "
    "ID, and contact details are shared only after a request is accepted."
)
ABOUT_FR = (
    "Trouver un bon colocataire n’est pas facile. Les étudiants cherchent dans des groupes Facebook, des annonces "
    "Kijiji et des conversations de groupe, sans moyen de comparer les gens, et des habitudes incompatibles "
    "mènent souvent à des conflits.\n\n"
    "RoomMate Finder jumelle les étudiants de l’Université de Windsor selon leur compatibilité, pas seulement le "
    "loyer : budget, secteur, horaire de sommeil, propreté et plus encore. Les étudiants vérifiés obtiennent un "
    "badge après la vérification de leur carte étudiante par un administrateur, et les coordonnées ne sont "
    "partagées qu’une fois la demande acceptée."
)
TEAM = [
    ("Mohammed Adil", "Profiles, search and matching", "Profils, recherche et compatibilité"),
    ("Nazim Ali Firdous", "Authentication and uploads", "Authentification et téléversements"),
    ("Alyan Khowaja", "Requests, history and design", "Demandes, historique et conception"),
]
FAQ = [
    ("How is the match score calculated?", "Comment le score de compatibilité est-il calculé ?",
     "From budget, preferred area, sleep schedule, cleanliness, pets, smoking and guests. It is calculated in Python on our server.",
     "À partir du budget, du secteur préféré, de l’horaire de sommeil, de la propreté, des animaux, du tabac et des invités. Il est calculé en Python sur notre serveur."),
    ("Who can see my student ID?", "Qui peut voir ma carte étudiante ?",
     "Only administrators. It is never shown on the site.",
     "Seulement les administrateurs. Elle n’est jamais affichée sur le site."),
    ("When are my contact details shared?", "Quand mes coordonnées sont-elles partagées ?",
     "Only after the other student accepts your roommate request.",
     "Seulement après que l’autre étudiant a accepté votre demande de colocation."),
]


def seed(apps, schema_editor):
    InfoPage = apps.get_model("matches", "InfoPage")
    TeamMember = apps.get_model("matches", "TeamMember")
    FAQItem = apps.get_model("matches", "FAQItem")
    InfoPage.objects.get_or_create(slug="about", defaults={
        "title": "About RoomMate Finder", "title_fr": "À propos de RoomMate Finder",
        "body": ABOUT_EN, "body_fr": ABOUT_FR})
    if not TeamMember.objects.exists():
        for i, (name, role, role_fr) in enumerate(TEAM):
            TeamMember.objects.create(name=name, role=role, role_fr=role_fr, order=i)
    if not FAQItem.objects.exists():
        for i, (q, q_fr, a, a_fr) in enumerate(FAQ):
            FAQItem.objects.create(question=q, question_fr=q_fr, answer=a, answer_fr=a_fr, order=i)


class Migration(migrations.Migration):
    dependencies = [("matches", "0002_site_content_and_indexes")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
