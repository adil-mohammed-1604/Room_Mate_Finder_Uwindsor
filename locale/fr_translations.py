"""French translations. Edit the right-hand side to change the French, then run:

    python locale/build_locale.py

(see the top of build_locale.py). Keys are the exact English texts used in the code.
Texts with %(name)s placeholders must keep the same placeholders in French.
Plural entries are (singular, plural) pairs.
"""

FR = {}

# ----- emails
FR.update({
    '\nAccept or decline it here: %(url)s\n\n%(site)s\n': '\nAcceptez ou refusez-la ici : %(url)s\n\n%(site)s\n',
    '\nTheir message: "%(message)s"\n': '\nSon message : « %(message)s »\n',
    'Hi %(receiver)s,\n\n%(sender)s sent you a roommate request on %(site)s.\n':
        'Bonjour %(receiver)s,\n\n%(sender)s vous a envoyé une demande de colocation sur %(site)s.\n',
    'Hi %(sender)s,\n\n%(receiver)s %(status)s your roommate request.\n\nSee your requests: %(url)s\n\n%(site)s\n':
        'Bonjour %(sender)s,\n\n%(receiver)s : votre demande de colocation est « %(status)s ».\n\nConsultez vos demandes : %(url)s\n\n%(site)s\n',
    'New roommate request from %(sender)s': 'Nouvelle demande de colocation de %(sender)s',
    'Your roommate request was %(status)s': 'Votre demande de colocation est : %(status)s',
    'Hi %(name)s,': 'Bonjour %(name)s,',
    'We received a request to reset the password for your %(brand)s account.':
        'Nous avons reçu une demande de réinitialisation du mot de passe de votre compte %(brand)s.',
    'Choose a new password here:': 'Choisissez un nouveau mot de passe ici :',
    'This link works for %(hours)s hours and can only be used once.':
        'Ce lien est valable %(hours)s heures et ne peut être utilisé qu’une seule fois.',
    "If you didn't ask for this, you can ignore this email and your password will stay the same.":
        'Si vous n’avez pas fait cette demande, ignorez ce message : votre mot de passe restera inchangé.',
    'Need help? Contact us at %(mail)s.': 'Besoin d’aide ? Écrivez-nous à %(mail)s.',
    'The %(brand)s team': 'L’équipe %(brand)s',
    'Reset your %(name)s password': 'Réinitialisez votre mot de passe %(name)s',
    "This link works for %(hours)s hours and can only be used once. If you didn't ask for this, ignore this email and your password will stay the same.":
        'Ce lien est valable %(hours)s heures et ne peut être utilisé qu’une seule fois. Si vous n’avez pas fait cette demande, ignorez ce message : votre mot de passe restera inchangé.',
    'Need help? Contact <a href="mailto:%(mail)s">%(mail)s</a>.': 'Besoin d’aide ? Écrivez à <a href="mailto:%(mail)s">%(mail)s</a>.',
})

# ----- navigation, footer, general
FR.update({
    'Home': 'Accueil', 'About': 'À propos', 'About Us': 'À propos de nous', 'Our Team': 'Notre équipe',
    'Our team': 'Notre équipe', 'Contact': 'Contact', 'FAQ': 'FAQ', 'Quick links': 'Liens rapides',
    'Follow us': 'Suivez-nous', 'COMP-8347 Group 8': 'COMP-8347 Groupe 8',
    "Helping University of Windsor students find roommates they'll actually get along with.":
        'Nous aidons les étudiants de l’Université de Windsor à trouver des colocataires avec qui ils s’entendront vraiment.',
    'My profile': 'Mon profil', 'Create profile': 'Créer mon profil', 'Staff panel': 'Panneau du personnel',
    'Requests': 'Demandes', 'Shortlist': 'Favoris', 'History': 'Historique', 'Logout': 'Déconnexion',
    'Login': 'Connexion', 'Sign up': 'Inscription',
    'Pending requests waiting for you': 'Demandes en attente de votre réponse',
    'Switch between light and dark mode': 'Passer du mode clair au mode sombre',
    'Light / dark mode': 'Mode clair / sombre',
    'Close': 'Fermer', 'Menu': 'Menu', 'Main menu': 'Menu principal', 'Pages': 'Pages',
    'Previous': 'Précédent', 'Next': 'Suivant', 'Page %(n)s of %(total)s': 'Page %(n)s sur %(total)s',
    'Cancel': 'Annuler', 'Save': 'Enregistrer', 'Edit': 'Modifier', 'Delete': 'Supprimer', 'Remove': 'Retirer',
    'Yes': 'Oui', 'No': 'Non', 'All': 'Tous', 'Any': 'Indifférent', 'Search': 'Rechercher', 'Apply': 'Appliquer',
    'Reset': 'Réinitialiser', 'Actions': 'Actions', 'Open': 'Ouvrir', 'Review': 'Examiner',
    'Not allowed': 'Accès refusé',
    "You don't have permission to open this page.": 'Vous n’avez pas la permission d’ouvrir cette page.',
    'Back to home': 'Retour à l’accueil',
})

# ----- home
FR.update({
    "Find a roommate you'll actually get along with": 'Trouvez un colocataire avec qui vous vous entendrez vraiment',
    'Search keywords...': 'Rechercher des mots-clés...', 'Budget': 'Budget', 'Lifestyle': 'Mode de vie', 'Area': 'Secteur',
    'Sort by': 'Trier par', 'Go': 'OK',
    'You are browsing as a guest: limited results and blurred photos.': 'Vous naviguez en tant qu’invité : résultats limités et photos floutées.',
    '<a href="%(login_url)s">Log in</a> or <a href="%(signup_url)s">sign up</a> to see everyone.':
        '<a href="%(login_url)s">Connectez-vous</a> ou <a href="%(signup_url)s">inscrivez-vous</a> pour voir tout le monde.',
    '1. Sign up &amp; verify': '1. Inscrivez-vous et vérifiez-vous',
    'Create an account, upload a photo and student ID.': 'Créez un compte, ajoutez une photo et votre carte étudiante.',
    '2. Set preferences': '2. Définissez vos préférences',
    'Budget, area, sleep schedule, cleanliness, pets.': 'Budget, secteur, horaire de sommeil, propreté, animaux.',
    '3. See match scores': '3. Consultez les scores de compatibilité',
    'Profiles ranked by compatibility.': 'Profils classés par compatibilité.',
    '4. Send a request': '4. Envoyez une demande',
    'Contact details are shared once accepted.': 'Les coordonnées sont partagées une fois la demande acceptée.',
    'Your profile is <strong>%(pct)s%%</strong> complete. A fuller profile gets better matches.':
        'Votre profil est complété à <strong>%(pct)s %%</strong>. Un profil plus complet donne de meilleures correspondances.',
    'Finish profile': 'Compléter le profil',
    'Verified': 'Vérifié', '%(score)s%% match': '%(score)s %% de compatibilité', '%(s)s%% match': '%(s)s %% de compatibilité',
    'Log in to see match %': 'Connectez-vous pour voir la compatibilité',
    'Program not set': 'Programme non indiqué', '$%(amount)s/mo': '%(amount)s $/mois', '$%(amount)s/month': '%(amount)s $/mois',
    'View profile': 'Voir le profil',
    'No profiles match your search. Try different keywords or clear the filters.':
        'Aucun profil ne correspond à votre recherche. Essayez d’autres mots-clés ou effacez les filtres.',
    'Clear filters': 'Effacer les filtres',
    'Best match': 'Meilleure compatibilité', 'Budget: low to high': 'Budget : croissant', 'Budget: high to low': 'Budget : décroissant',
    'Newest first': 'Plus récents d’abord', 'Under $600': 'Moins de 600 $', 'Over $1,200': 'Plus de 1 200 $',
})

# ----- info pages
FR.update({
    'About RoomMate Finder': 'À propos de RoomMate Finder',
            'Frequently asked questions': 'Questions fréquentes',
                            'Our team (Group 8, COMP-8347)': 'Notre équipe (Groupe 8, COMP-8347)',
                'Contact us': 'Contactez-nous', 'Send message': 'Envoyer le message',
})

# ----- sign up, login, passwords
FR.update({
    'Welcome back': 'Bon retour', 'Log in to see your matches and requests.': 'Connectez-vous pour voir vos correspondances et vos demandes.',
    'Forgot your password?': 'Mot de passe oublié ?',
    'New here? <a href="%(signup_url)s">Create an account</a>': 'Nouveau ici ? <a href="%(signup_url)s">Créez un compte</a>',
    'Create your account': 'Créez votre compte',
    "Join %(site)s to find a roommate you'll get along with.": 'Rejoignez %(site)s pour trouver un colocataire avec qui vous vous entendrez.',
    'Already have an account? <a href="%(login_url)s">Login</a>': 'Vous avez déjà un compte ? <a href="%(login_url)s">Connectez-vous</a>',
    'Password changed': 'Mot de passe modifié', 'You can now log in with your new password.': 'Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.',
    'New password': 'Nouveau mot de passe', 'Choose a new password': 'Choisissez un nouveau mot de passe',
    'Link no longer valid': 'Lien non valide', 'Change password': 'Changer le mot de passe',
    'This reset link is invalid or has already been used.': 'Ce lien de réinitialisation est invalide ou a déjà été utilisé.',
    'Request a new link': 'Demander un nouveau lien', 'Check your email': 'Vérifiez vos courriels',
    'If an account exists for that email, a reset link has been sent. The link works for a limited time.':
        'Si un compte existe pour cette adresse, un lien de réinitialisation a été envoyé. Le lien est valable pour une durée limitée.',
    'Development mode: the email is printed in the terminal running the server.': 'Mode développement : le courriel s’affiche dans le terminal où le serveur fonctionne.',
    'Questions? Contact <a href="mailto:%(mail)s">%(mail)s</a>.': 'Des questions ? Écrivez à <a href="mailto:%(mail)s">%(mail)s</a>.',
    'Back to login': 'Retour à la connexion', 'Reset password': 'Réinitialiser le mot de passe',
    'Reset your password': 'Réinitialisez votre mot de passe',
    "Enter your email and we'll send you a reset link.": 'Saisissez votre adresse e-mail et nous vous enverrons un lien de réinitialisation.',
    'Send reset link': 'Envoyer le lien', 'Email': 'E-mail', 'Password': 'Mot de passe', 'Confirm password': 'Confirmer le mot de passe',
    'An account with this email already exists.': 'Un compte avec cette adresse e-mail existe déjà.',
    'A user with this email already exists.': 'Un utilisateur avec cette adresse e-mail existe déjà.',
    'Please enter a correct email and password. Both fields may be case-sensitive.':
        'Veuillez saisir une adresse e-mail et un mot de passe valides. Les deux champs peuvent être sensibles à la casse.',
})

# ----- profile
FR.update({
    'Create your profile': 'Créez votre profil', 'Edit your profile': 'Modifiez votre profil', 'About you': 'À propos de vous',
    'Save profile': 'Enregistrer le profil', 'Delete profile': 'Supprimer le profil', 'Delete your profile?': 'Supprimer votre profil ?',
    'This removes your profile and lifestyle preferences. Your account stays active.': 'Votre profil et vos préférences de mode de vie seront supprimés. Votre compte reste actif.',
    'Yes, delete': 'Oui, supprimer',
    'Full name': 'Nom complet', 'Program': 'Programme', 'Bio': 'Présentation', 'Phone': 'Téléphone', 'Photo': 'Photo',
    'Preferred area': 'Secteur préféré', 'Monthly budget in CAD': 'Budget mensuel en CAD',
    'Sleep schedule': 'Horaire de sommeil', 'Cleanliness': 'Propreté', 'Pets': 'Animaux', 'Smoking': 'Tabac',
    'Guests often': 'Invités fréquents', 'Guests': 'Invités',
    'Early bird': 'Lève-tôt', 'Night owl': 'Couche-tard', 'Flexible': 'Flexible',
    'Have pets': 'A des animaux', 'Fine with pets': 'Accepte les animaux', 'No pets': 'Pas d’animaux',
    '1 = relaxed, 5 = very tidy': '1 = décontracté, 5 = très ordonné', 'Must be between 1 and 5.': 'Doit être compris entre 1 et 5.',
    'Budget must be greater than 0.': 'Le budget doit être supérieur à 0.',
    'Photo too large (max 2 MB).': 'Photo trop volumineuse (2 Mo max).', 'Photo must be a JPG or PNG.': 'La photo doit être au format JPG ou PNG.',
    'Welcome! Create your profile to get started.': 'Bienvenue ! Créez votre profil pour commencer.',
    'Your profile has been created.': 'Votre profil a été créé.', 'Your profile has been updated.': 'Votre profil a été mis à jour.',
    'Your profile has been deleted.': 'Votre profil a été supprimé.', 'Create your profile first.': 'Créez d’abord votre profil.',
    'You are already a Verified Student.': 'Vous êtes déjà un étudiant vérifié.',
    'Student ID uploaded. An admin will review it soon.': 'Carte étudiante envoyée. Un administrateur l’examinera bientôt.',
    'Get verified': 'Faites-vous vérifier', 'Verify your student ID': 'Vérifiez votre carte étudiante',
    'Upload a photo or PDF of your student ID (JPG, PNG or PDF, max 5 MB). Only administrators can see it.':
        'Téléversez une photo ou un PDF de votre carte étudiante (JPG, PNG ou PDF, 5 Mo max). Seuls les administrateurs peuvent la voir.',
    'Latest submission:': 'Dernier envoi :', 'Your document is waiting for review.': 'Votre document attend d’être examiné.',
    'Upload': 'Téléverser',
    'Student ID file': 'Fichier de la carte étudiante', 'Only JPG, PNG or PDF files are allowed.': 'Seuls les fichiers JPG, PNG ou PDF sont acceptés.',
    'File too large (max 5 MB).': 'Fichier trop volumineux (5 Mo max).',
    'Pending': 'En attente', 'Approved': 'Approuvé', 'Rejected': 'Refusé',
})

# ----- profile page, shortlist, compare
FR.update({
    'Verified Student': 'Étudiant vérifié', 'Budget:': 'Budget :', 'Preferred area:': 'Secteur préféré :', 'About:': 'À propos :',
    'Profile completeness': 'Profil complété', 'Still to do:': 'Reste à faire :', 'Your profile is complete.': 'Votre profil est complet.',
    'Why you match: %(s)s%%': 'Pourquoi vous êtes compatibles : %(s)s %%',
    "Only budget and area are compared, because one of you hasn't filled in lifestyle answers yet.":
        'Seuls le budget et le secteur sont comparés, car l’un de vous n’a pas encore rempli ses réponses sur le mode de vie.',
    'Sleep schedule:': 'Horaire de sommeil :', 'Cleanliness:': 'Propreté :', 'Pets:': 'Animaux :', 'Smoking:': 'Tabac :',
    'Guests often:': 'Invités fréquents :',
    'Contact details:': 'Coordonnées :', 'Email:': 'E-mail :', 'Phone:': 'Téléphone :', 'not provided': 'non indiqué',
    'Edit my profile': 'Modifier mon profil', 'Request %(status)s': 'Demande : %(status)s', 'View requests': 'Voir les demandes',
    'Send roommate request': 'Envoyer une demande de colocation', 'Saved (remove)': 'Enregistré (retirer)',
    'Save to shortlist': 'Ajouter aux favoris',
    '<a href="%(login_url)s">Log in</a> or <a href="%(signup_url)s">sign up</a> to see the full profile and send a request.':
        '<a href="%(login_url)s">Connectez-vous</a> ou <a href="%(signup_url)s">inscrivez-vous</a> pour voir le profil complet et envoyer une demande.',
    'My shortlist': 'Mes favoris', 'Download CSV': 'Télécharger en CSV',
    'Tick two students and press <strong>Compare</strong> to see them side by side.': 'Cochez deux étudiants et appuyez sur <strong>Comparer</strong> pour les voir côte à côte.',
    'Compare %(name)s': 'Comparer %(name)s', 'Any area': 'Tous secteurs', 'Browse profiles': 'Parcourir les profils',
    'Your shortlist is empty. Save profiles from their profile page.': 'Vos favoris sont vides. Ajoutez des profils depuis leur page.',
    'Compare (pick 2)': 'Comparer (choisir 2)', 'Compare profiles': 'Comparer les profils', 'Back to shortlist': 'Retour aux favoris',
    'Greyed rows are the same for both students.': 'Les lignes grisées sont identiques pour les deux étudiants.',
    'Match with you': 'Compatibilité avec vous',
    'Added to your shortlist.': 'Ajouté à vos favoris.', 'Already in your shortlist.': 'Déjà dans vos favoris.',
    'Removed from your shortlist.': 'Retiré de vos favoris.',
    "You can't save your own profile.": 'Vous ne pouvez pas enregistrer votre propre profil.',
    'Pick exactly two profiles from your shortlist to compare.': 'Choisissez exactement deux profils parmi vos favoris à comparer.',
    '$%(a)s vs $%(b)s per month': '%(a)s $ contre %(b)s $ par mois', '%(a)s vs %(b)s': '%(a)s contre %(b)s',
    'Name and budget': 'Nom et budget', 'Profile photo': 'Photo de profil', 'Short bio': 'Courte présentation',
    'Program of study': 'Programme d’études',
    'Phone number': 'Numéro de téléphone', 'Lifestyle answers': 'Réponses sur le mode de vie',
    'Verified student ID': 'Carte étudiante vérifiée',
    'Budget (CAD/month)': 'Budget (CAD/mois)', 'Name': 'Nom', 'Match %': 'Compatibilité %', 'Saved on': 'Ajouté le',
    'Visited at': 'Visité le', 'Page': 'Page',
})

# ----- requests, history, contact
FR.update({
    'My requests': 'Mes demandes', 'Roommate requests': 'Demandes de colocation', 'Received': 'Reçues', 'Sent': 'Envoyées',
    'Accept': 'Accepter', 'Decline': 'Refuser', 'Withdraw': 'Retirer', 'No requests received yet.': 'Aucune demande reçue pour le moment.',
    "You haven't sent any requests.": 'Vous n’avez envoyé aucune demande.',
    'Send request': 'Envoyer la demande', 'Send a request to %(name)s': 'Envoyer une demande à %(name)s', 'Message': 'Message',
    'Introduce yourself (optional)': 'Présentez-vous (facultatif)',
    'Accepted': 'Acceptée', 'Declined': 'Refusée', 'Withdrawn': 'Retirée',
    "You can't send a request to yourself.": 'Vous ne pouvez pas vous envoyer une demande.',
    'Create your profile before sending requests.': 'Créez votre profil avant d’envoyer des demandes.',
    'You already have an active request with this student.': 'Vous avez déjà une demande active avec cet étudiant.',
    'Roommate request sent.': 'Demande de colocation envoyée.',
    'Request %(status)s.': 'Demande : %(status)s.',
    'Thanks! Your message has been sent.': 'Merci ! Votre message a été envoyé.',
    'Subject': 'Objet', 'Please write at least 10 characters.': 'Veuillez écrire au moins 10 caractères.',
    'My history': 'Mon historique', 'Last visit:': 'Dernière visite :', 'This is your first visit.': 'C’est votre première visite.',
    'Page views per day': 'Pages vues par jour', 'Date': 'Date', 'Page views': 'Pages vues',
    'No visits recorded yet.': 'Aucune visite enregistrée.',
    'Recently viewed profiles': 'Profils consultés récemment',
    "You haven't viewed any profiles in this session.": 'Vous n’avez consulté aucun profil pendant cette session.',
})

# ----- staff panel
FR.update({
    'Overview': 'Aperçu', 'People': 'Personnes', 'Moderation': 'Modération', 'Data': 'Données', 'View site': 'Voir le site',
    'Django admin': 'Admin Django', 'What is happening on the site right now.': 'Ce qui se passe sur le site en ce moment.',
    '%(n)s this week': '%(n)s cette semaine', '%(n)s views': '%(n)s pages vues',
    'Page views, last 14 days': 'Pages vues, 14 derniers jours',
    'Sign-ups, last 14 days': 'Inscriptions, 14 derniers jours', 'total': 'total',
    'Student ID review': 'Examen des cartes étudiantes',
    'Review pending IDs': 'Examiner les cartes en attente', 'Needs your attention': 'Demande votre attention',
    'All caught up.': 'Tout est à jour.',
    'Recent activity': 'Activité récente', 'Nothing has happened yet.': 'Rien ne s’est encore passé.', '%(t)s ago': 'il y a %(t)s',
    'Users': 'Utilisateurs', 'Profiles': 'Profils', 'Pending IDs': 'Cartes en attente', 'Open messages': 'Messages ouverts',
    'Lifestyle preferences': 'Préférences de mode de vie', 'Verification': 'Vérification',
    'Contact messages': 'Messages de contact',
    'Areas': 'Secteurs', 'Shortlists': 'Favoris', 'Visit log': 'Journal des visites',
    'Add user': 'Ajouter un utilisateur', 'Edit user': 'Modifier l’utilisateur', 'Delete user': 'Supprimer l’utilisateur',
    'Add profile': 'Ajouter un profil', 'Edit profile': 'Modifier le profil',
    'Add lifestyle preference': 'Ajouter une préférence de mode de vie',
    'Edit lifestyle preference': 'Modifier la préférence de mode de vie',
    'Delete lifestyle preference': 'Supprimer la préférence de mode de vie',
    'Add verification': 'Ajouter une vérification', 'Review verification': 'Examiner la vérification',
    'Delete verification': 'Supprimer la vérification',
    'Add message': 'Ajouter un message', 'Open message': 'Ouvrir le message', 'Delete message': 'Supprimer le message',
    'Add request': 'Ajouter une demande', 'Edit request': 'Modifier la demande', 'Delete request': 'Supprimer la demande',
    'Add area': 'Ajouter un secteur', 'Edit area': 'Modifier le secteur', 'Delete area': 'Supprimer le secteur',
    'Add shortlist entry': 'Ajouter un favori', 'Edit shortlist entry': 'Modifier le favori',
    'Delete shortlist entry': 'Supprimer le favori',
    'Add visit': 'Ajouter une visite', 'Edit visit': 'Modifier la visite', 'Delete visit': 'Supprimer la visite',
    'Not verified': 'Non vérifié', 'Resolved': 'Résolu', 'Type to search…': 'Saisissez pour rechercher…',
    'Shortcut: n': 'Raccourci : n',
    'selected': 'sélectionné(s)', 'Select all': 'Tout sélectionner', 'Select row': 'Sélectionner la ligne',
    'Delete the selected records? This cannot be undone.': 'Supprimer les enregistrements sélectionnés ? Cette action est irréversible.',
    'Nothing here yet.': 'Rien ici pour le moment.',
    'Approve': 'Approuver', 'Reject': 'Refuser', 'Mark resolved': 'Marquer comme résolu', 'Reopen': 'Rouvrir',
    'Resolve': 'Résoudre',
    'View ID': 'Voir la carte', 'Open student ID': 'Ouvrir la carte étudiante',
    "You are about to delete <strong>%(name)s</strong>. Anything that depends on it (for example a user's profile, requests and uploads records) is deleted too. This cannot be undone.":
        'Vous êtes sur le point de supprimer <strong>%(name)s</strong>. Tout ce qui en dépend (par exemple le profil, les demandes et les envois d’un utilisateur) sera aussi supprimé. Cette action est irréversible.',
    'Record created.': 'Enregistrement créé.', 'Record saved.': 'Enregistrement sauvegardé.',
    'Record deleted.': 'Enregistrement supprimé.',
    'That would duplicate an existing record.': 'Cela créerait un doublon d’un enregistrement existant.',
    'That change would duplicate an existing record (for example two active requests between the same people).':
        'Ce changement créerait un doublon d’un enregistrement existant (par exemple deux demandes actives entre les mêmes personnes).',
    'You cannot delete your own account from the panel.': 'Vous ne pouvez pas supprimer votre propre compte depuis le panneau.',
    'ID %(status)s for %(who)s.': 'Carte étudiante de %(who)s : %(status)s.',
    'Message marked as resolved.': 'Message marqué comme résolu.', 'Message reopened.': 'Message rouvert.',
    'Tick at least one row first.': 'Cochez d’abord au moins une ligne.',
    'New password (leave empty to keep the current one)': 'Nouveau mot de passe (laisser vide pour conserver l’actuel)',
    'Password is required for a new user.': 'Un mot de passe est obligatoire pour un nouvel utilisateur.',
    'The two passwords do not match.': 'Les deux mots de passe ne correspondent pas.',
    '%(who)s joined': '%(who)s s’est inscrit(e)',
    '%(sender)s sent a request to %(receiver)s': '%(sender)s a envoyé une demande à %(receiver)s',
    '%(name)s wrote: %(subject)s': '%(name)s a écrit : %(subject)s',
    '%(who)s uploaded a student ID': '%(who)s a envoyé une carte étudiante',
})

# ----- plurals: (singular, plural)
FR.update({
    '%(n)d record updated.': ('%(n)d enregistrement mis à jour.', '%(n)d enregistrements mis à jour.'),
    '%(n)d record was skipped (protected account).': ('%(n)d enregistrement ignoré (compte protégé).', '%(n)d enregistrements ignorés (comptes protégés).'),
    '%(n)s record': ('%(n)s enregistrement', '%(n)s enregistrements'),
})

# ----- field names shown in the panel (looked up while the site runs, so the scanner cannot see them)
FR.update({
    'Email address': 'Adresse e-mail', 'User': 'Utilisateur', 'Is verified': 'Vérifié', 'Created at': 'Créé le',
    'Updated at': 'Modifié le', 'Uploaded at': 'Envoyé le', 'Reviewed at': 'Examiné le',
    'Admin notes': 'Notes de l’administrateur',
    'Status': 'Statut', 'Sender': 'Expéditeur', 'Receiver': 'Destinataire', 'Responded at': 'Réponse le',
    'Is resolved': 'Résolu',
    'Saved at': 'Ajouté le', 'Path': 'Chemin', 'Description': 'Description', 'Profile': 'Profil',
    'Student id': 'Carte étudiante',
})

# ----- site content, filters and customization
FR.update({
    '%(n)s days': '%(n)s jours',
    'About page': 'Page À propos',
    'Add page': 'Ajouter une page',
    'Add question': 'Ajouter une question',
    'Add team member': 'Ajouter un membre',
    'Answer': 'Réponse',
    'Answer (French)': 'Réponse (français)',
    'Delete page': 'Supprimer la page',
    'Delete question': 'Supprimer la question',
    'Delete team member': 'Supprimer le membre',
    'Edit About page': 'Modifier la page À propos',
    'Edit question': 'Modifier la question',
    'Edit team member': 'Modifier le membre',
    'Filter by status': 'Filtrer par statut',
    'No requests match this filter.': 'Aucune demande ne correspond à ce filtre.',
    'Order': 'Ordre',
    'Question': 'Question',
    'Question (French)': 'Question (français)',
    'Role': 'Rôle',
    'Role (French)': 'Rôle (français)',
    'Separate paragraphs with a blank line.': 'Séparez les paragraphes par une ligne vide.',
    'Shown on the FAQ page': 'Affichée sur la page FAQ',
    'Shown on the Team page': 'Affiché sur la page Équipe',
    'Site content': 'Contenu du site',
    'Team members': 'Membres de l’équipe',
    'Text': 'Texte',
    'Text (French)': 'Texte (français)',
    'This student already sent you a request. Reply to it here.':
        'Cet étudiant vous a déjà envoyé une demande. Répondez-y ici.',
    'Time range': 'Période',
    'Title': 'Titre',
    'Title (French)': 'Titre (français)',
})

DYNAMIC = [
    'Email address', 'User', 'Is verified', 'Created at', 'Updated at', 'Uploaded at', 'Reviewed at', 'Admin notes',
    'Status', 'Sender', 'Receiver', 'Responded at', 'Is resolved', 'Saved at', 'Path', 'Description', 'Profile',
    'Student id',
    # footer texts that now come from settings.SITE_FOOTER (translated at runtime)
    "Helping University of Windsor students find roommates they'll actually get along with.",
    'COMP-8347 Group 8',
]
