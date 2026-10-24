# RoomMate Finder

A Django web app that helps university students find compatible roommates using lifestyle-based match scores, search filters, and verified student profiles.

Built by **Group 8** for **COMP-8347: Internet Applications and Distributed Systems** at the University of Windsor.

> **Status:** In development (Fall 2026)

---

## About the Project

Finding a good roommate is hard. Students search across Facebook groups, Kijiji posts, and group chats with no easy way to compare people, and mismatched habits often lead to conflict and early move-outs. It is also difficult to know whether a profile belongs to a real student.

**RoomMate Finder** solves this by matching students on compatibility, not just rent:

1. **Sign up and verify:** create an account and upload a photo and student ID.
2. **Set preferences:** budget, preferred area, sleep schedule, cleanliness, pets, and more.
3. **See match scores:** other students are ranked by a compatibility percentage.
4. **Send a request:** contact details are shared only after a request is accepted.

Verified students receive a **Verified Student** badge after admin approval.

---

## Features

### For visitors (not logged in)
- "How it works" overview on the home page
- Browse sample profiles with limited details and blurred photos
- Search with keyword and dropdown filters (limited results)
- About Us, Contact Us, Team, and FAQ pages

### For registered students
- Create, view, edit, and delete a detailed profile
- Upload a profile photo and a private student ID for verification
- See full profiles with compatibility scores
- Send, accept, decline, and withdraw roommate requests
- Save profiles to a personal shortlist
- **My History** page showing visits per day, last visit, and recently viewed profiles

### Core Django features
| Feature | Implementation |
|---|---|
| Models & CRUD | Profiles, roommate requests, saved shortlist |
| Class-based views | Home as `ListView`, profile page as `DetailView` |
| Forms | Sign-up, profile, lifestyle, ID upload, request, contact |
| Authentication | Login, logout, and forgot password (Django auth) |
| Search | Keyword search plus budget, lifestyle, and area dropdowns |
| Sessions & cookies | Visit tracking and recently viewed profiles |
| File uploads | Profile photos and student ID documents |
| Fixtures | Initial data loaded from JSON |
| Styling | Bootstrap 5 with a custom theme and full footer |

---

## Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, Bootstrap 5
- **Database:** SQLite (initial data via JSON fixtures)
- **IDE:** PyCharm
- **Version control:** Git and GitHub

---

## Getting Started

### Prerequisites
- Python 3.10 or newer
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/adil-mohammed-1604/Room_Mate_Finder_Uwindsor.git
   cd Room_Mate_Finder_Uwindsor
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

5. **Load initial data**
   ```bash
   python manage.py loaddata initial_data
   ```

6. **Create an admin account** (used to approve student ID verification)
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

   Open http://127.0.0.1:8000 in your browser.

> **Password reset in development:** emails are printed to the terminal using Django's console email backend, so no email service is needed.

---

## Project Structure

```
Room_Mate_Finder_Uwindsor/
├── roommate_finder/     # Project settings and main URLs
├── profiles/            # Profiles, areas, search, matching, saved shortlist
├── accounts/            # Sign-up, login, logout, password reset, uploads
├── matches/             # Roommate requests, user history, contact pages
├── templates/           # Base template, navbar, footer, shared pages
├── static/              # CSS, images, JavaScript
├── fixtures/            # JSON initial data
├── media/               # Uploaded files (not tracked by Git)
├── requirements.txt
└── manage.py
```

---

## Team and Responsibilities

| Member | Area | Responsibilities |
|---|---|---|
| **Mohammed Adil** | Profiles, Search & Matching | `Profile`, `Area`, `SavedProfile` models; home `ListView` and profile `DetailView`; search with dropdown filters; compatibility score; saved shortlist; JSON fixtures |
| **Nazim Ali Firdous** | Authentication & Uploads | `LifestylePreference`, `VerificationDocument` models; sign-up, login, logout, forgot password; profile CRUD; photo and student ID upload; admin verification |
| **Alyan Khowaja** | Requests, History & Design | `RoommateRequest`, `VisitLog`, `ContactMessage` models; roommate request cycle; My History page with sessions and cookies; Contact, About, and Team pages; footer and Bootstrap theme |

---

## Contributing (Team Workflow)

Each member works on their own feature branch and merges into `main` through a pull request.

```bash
git checkout main
git pull
git checkout -b feature/your-feature-name
```

**Branch names**
- `feature/profiles-search`: Mohammed
- `feature/auth-uploads`: Nazim
- `feature/requests-history`: Alyan

**Commit messages** should be short and descriptive, for example:
- `Added Area model and budget dropdown filter`
- `Implemented password reset templates`
- `Added VisitLog session tracking`

Commit small changes often, and pull from `main` regularly to avoid conflicts.

---

## Testing

Run the test suite with:

```bash
python manage.py test
```

Edge cases covered include empty searches, invalid filter values, wrong logins, duplicate sign-ups, invalid or oversized uploads, duplicate roommate requests, and empty form submissions.

---

## Development Plan

| Phase | Work |
|---|---|
| Weeks 1–5 | Repository and project setup, models, fixtures, base template |
| Weeks 6–7 | Class-based views, search and dropdowns, authentication, profile CRUD |
| Weeks 8–9 | Uploads, roommate requests, sessions and cookies history |
| Week 10 | Testing, edge cases, UI polish, rehearsal |
| Week 11 | Project defense with live demo |

---

## Privacy

- Student ID documents are visible only to administrators.
- Contact details are shared only after a roommate request is accepted.
- Uploaded files are stored locally and excluded from version control.

---

## Course Information

- **Course:** COMP-8347, Internet Applications and Distributed Systems
- **University:** University of Windsor
- **Term:** Fall 2026
- **Group:** 8
