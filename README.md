# Classroom Feedback System — Django + DRF Authentication & RBAC Demo

This submission demonstrates a complete classroom feedback system built with Django and Django REST Framework, showcasing JWT-based authentication and role-based access control (RBAC) for teaching purposes.

---

## 📋 Project Overview

### What This Is

A production-adjacent Django + DRF backend that implements a three-role classroom system:

- **Instructor** — Creates assignments, views all their student submissions, leaves feedback
- **Student** — Views their enrolled assignments, submits work, views feedback on their submissions
- **Observer** — (e.g., parent, guardian, or admin) reads a filtered view of one specific student's progress

### Why This Design?

This demo is built to teach learners:

1. How JWT tokens work and why they're preferred over session cookies in APIs
2. The difference between **authentication** (who are you?) and **authorization** (what are you allowed to do?)
3. How to implement **role-based access control** using custom DRF permission classes
4. The subtle-but-critical difference between **role-level** and **row-level** permissions (Observer can see _only_ their linked student)

---

## 🚀 Quick Start

### Live Demo (Backend Only)

**Live URL:** [Add deployed URL here — see Deployment section below]

**Demo Credentials:**

| Role       | Email                 | Password    |
| ---------- | --------------------- | ----------- |
| Instructor | `instructor@demo.dev` | `Demo@1234` |
| Student    | `student@demo.dev`    | `Demo@1234` |
| Observer   | `observer@demo.dev`   | `Demo@1234` |

All demo data is pre-seeded with sample assignments and submissions. See [Local Setup](#-local-setup) → [Running the Seed Command](#running-the-seed-command) for details.

---

## 💻 Local Setup

### Prerequisites

- Python 3.10+
- pip or poetry
- Git

### 1. Clone and Enter the Repository

```bash
git clone <your-repo-url>
cd classroom-feedback-api
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**What's included:**

- Django 6.0.5
- Django REST Framework 3.17.1
- djangorestframework-simplejwt 5.5.1 (for JWT auth)
- PyJWT 2.13.0

### 4. Apply Migrations

```bash
python manage.py migrate
```

### 5. Running the Seed Command

Populate the database with demo accounts, assignments, submissions, and Observer-Student linkages:

```bash
python manage.py seed
```

This creates:

- 1 Instructor (`instructor@demo.dev`)
- 1 Student (`student@demo.dev`)
- 1 Observer (`observer@demo.dev`)
- 2 Assignments (created by the instructor)
- 2+ Submissions (submitted by the student)
- 1 Observer→Student link (Observer can only see this specific student's submissions)

### 6. Run the Development Server

```bash
python manage.py runserver
```

Server will be available at `http://localhost:8000/`

---

## 🔗 API Endpoints

All endpoints require a valid JWT `access` token in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

### Authentication

| Method | Endpoint                | Description                     | Requires Auth? |
| ------ | ----------------------- | ------------------------------- | -------------- |
| POST   | `/api/v1/auth/login/`   | Obtain access + refresh tokens  | No             |
| POST   | `/api/v1/auth/refresh/` | Refresh an expired access token | No             |

**Login Request:**

```json
{
  "email": "instructor@demo.dev",
  "password": "Demo@1234"
}
```

**Login Response:**

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Assignments

| Method | Endpoint               | Description                         | Allowed Roles                 |
| ------ | ---------------------- | ----------------------------------- | ----------------------------- |
| GET    | `/api/v1/assignments/` | List assignments (filtered by role) | Instructor, Student, Observer |
| POST   | `/api/v1/assignments/` | Create new assignment               | Instructor only               |

**Filtering:**

- **Instructor** — sees only their own assignments
- **Student** — sees all assignments (in production, would be filtered to enrolled courses)
- **Observer** — sees all assignments

### Submissions

| Method    | Endpoint                             | Description                         | Allowed Roles                                                                                    |
| --------- | ------------------------------------ | ----------------------------------- | ------------------------------------------------------------------------------------------------ |
| GET       | `/api/v1/submissions/`               | List submissions (filtered by role) | Instructor, Student, Observer                                                                    |
| POST      | `/api/v1/submissions/`               | Create new submission               | Student only                                                                                     |
| GET/PATCH | `/api/v1/submissions/{id}/feedback/` | View/update submission feedback     | Instructor only (for own assignments); Student (own submissions); Observer (linked student only) |

**Filtering:**

- **Instructor** — sees submissions only for their assignments
- **Student** — sees only their own submissions
- **Observer** — sees submissions only from their linked student (row-level check)

---

## 🔐 Security & Access Control

### How Permissions Work

Three layers of protection ensure users only see what they should:

#### 1. Role-Level Permissions (`IsInstructor`, `IsStudent`, `IsObserver`)

Defined in `accounts/permissions.py`. Checked first: "Does this user have the right role?"

```python
class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "instructor"
```

#### 2. Queryset Filtering

In views (e.g., `submissions/views.py`), `get_queryset()` filters results by role:

```python
def get_queryset(self):
    user = self.request.user
    if user.role == "student":
        return Submission.objects.filter(student=user)
    if user.role == "observer":
        linked = ObserverStudentLink.objects.get(observer=user)
        return Submission.objects.filter(student=linked.student)
    ...
```

#### 3. Row-Level Permission Checks (Observer Example)

The Observer role demonstrates why row-level checks matter. An Observer is not just "allowed to see submissions" — they're allowed to see submissions from **one specific linked student only**.

**Without row-level checks:** An Observer with the `IsObserver` permission could potentially access another observer's student data.

**With row-level checks:** `ObserverStudentLink` links each observer to exactly one student. `get_queryset()` enforces this by filtering: `Submission.objects.filter(student=linked.student)`.

#### 4. User Identity Enforcement

Critical: we never trust the client to tell us who the user is. In creation views:

```python
# assignments/views.py — CreateAssignmentView.perform_create()
def perform_create(self, serializer):
    # Never trust frontend. Always use request.user (from verified JWT).
    serializer.save(instructor=self.request.user)
```

Even if a malicious user sends `{"instructor_id": 999}`, we ignore it and use `self.request.user` from the JWT token.

---

## 🧪 Testing the System with Postman

### Workflow: Instructor Creates Assignment, Student Submits, Observer Watches

1. **Login as Instructor**
   - POST `/api/v1/auth/login/`
   - Email: `instructor@demo.dev`, Password: `Demo@1234`
   - Copy the `access` token

2. **Create Assignment (as Instructor)**
   - POST `/api/v1/assignments/`
   - Header: `Authorization: Bearer <access_token>`
   - Body:
     ```json
     {
       "title": "Advanced Django",
       "description": "Build a REST API with custom permissions"
     }
     ```

3. **Login as Student**
   - POST `/api/v1/auth/login/`
   - Email: `student@demo.dev`, Password: `Demo@1234`
   - Copy the new `access` token

4. **Submit Work (as Student)**
   - POST `/api/v1/submissions/`
   - Header: `Authorization: Bearer <access_token>`
   - Body:
     ```json
     {
       "assignment": 1,
       "content": "My solution to the advanced Django exercise"
     }
     ```

5. **Login as Observer**
   - POST `/api/v1/auth/login/`
   - Email: `observer@demo.dev`, Password: `Demo@1234`

6. **View Student's Submissions (as Observer)**
   - GET `/api/v1/submissions/`
   - Header: `Authorization: Bearer <access_token>`
   - You should see only the linked student's submissions

---

## 🏗️ Project Structure

```
classroom-feedback-api/
├── README.md                           # This file
├── manage.py                           # Django CLI
├── requirements.txt                    # Python dependencies
├── db.sqlite3                          # SQLite database (local dev only)
├── .gitignore                          # Git ignore rules
│
├── config/                             # Django project settings
│   ├── __init__.py
│   ├── settings.py                     # Database, installed apps, JWT config
│   ├── urls.py                         # Main URL router
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/                           # User model & authentication
│   ├── models.py                       # User, UserManager, UserRoles, ObserverStudentLink
│   ├── admin.py                        # Django admin registration
│   ├── permissions.py                  # IsInstructor, IsStudent, IsObserver
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── management/
│   │   └── commands/
│   │       └── seed.py                 # ← TEACHING COMMENT LOCATION #1
│   └── migrations/
│
├── auths/                              # Authentication endpoints
│   ├── views.py                        # LoginView, RefreshView (simplejwt)
│   ├── urls.py
│   └── serializers.py
│
├── assignments/                        # Assignment creation & listing
│   ├── models.py                       # Assignment model
│   ├── views.py                        # Create, list endpoints
│   ├── serializers.py
│   ├── urls.py
│   └── migrations/
│
├── submissions/                        # Submission creation & feedback
│   ├── models.py                       # Submission model
│   ├── views.py                        # Create, list, feedback endpoints
│   ├── serializers.py
│   ├── urls.py
│   └── migrations/
│
└── teaching-package/                   # Part 2: Teaching materials
    ├── 01-session-outline.md
    ├── 02-learning-objectives.md
    ├── 03-concept-explainers.md
    └── 04-anticipated-misconceptions.md
```

---

## 🎓 Teaching Comments & Design Decisions

**Where to find teaching comments:**

The code includes at least one deliberate teaching comment (addressed to learners) explaining a non-obvious security decision:

- **Location:** `accounts/management/commands/seed.py` — explains why the seed command clears existing data
- **Location:** `assignments/views.py` — `perform_create()` method — explains why we never trust `request.data` for user identity

---

## ⚠️ How to Break This App (Security Risks & Limitations)

### Risk #1: No Rate Limiting on Login Endpoint

**What's wrong:**
The login endpoint at `POST /api/v1/auth/login/` has no rate limiting. An attacker can brute-force credentials by sending thousands of login requests per second.

**Current implementation:** None. Any unauthenticated client can hit the endpoint unlimited times.

**Production fix:**

- Implement rate limiting using `django-ratelimit` or `djangorestframework-throttling`
- Example: 5 login attempts per minute per IP address
- After N failed attempts, lock the account temporarily or require CAPTCHA

```python
from rest_framework.throttling import AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
    # In settings: REST_FRAMEWORK['THROTTLES'] = {'login': '5/min'}
```

---

### Risk #2: Unlinked Observers Crash the System

**What's wrong:**
In `submissions/views.py`, when an Observer tries to view their submissions, the code uses:

```python
linked = ObserverStudentLink.objects.get(observer=user)  # DANGER: Crashes if not found
```

**The problem:** If an Observer is created but the database link to their student is missing (e.g., due to a bug, race condition, or manual database edit), this `.get()` call will **crash with a 500 error** instead of gracefully returning empty results.

**Why this is bad:**

1. An attacker could manually create an Observer account without a link, then query `/api/v1/submissions/`. The system crashes.
2. An administrator deletes the link but forgets to delete the Observer. System crashes.
3. Instead of denying access cleanly, you leak internal error information to the attacker.

**Current broken code:**

```python
def get_queryset(self):
    if user.role == "observer":
        linked = ObserverStudentLink.objects.get(observer=user)  # ❌ Crashes here
        return Submission.objects.filter(student=linked.student)
```

**Production fix:**

Use `.filter().first()` to safely check if the link exists:

```python
def get_queryset(self):
    if user.role == "observer":
        linked = ObserverStudentLink.objects.filter(observer=user).first()
        if not linked:
            return Submission.objects.none()  # ✅ Safe: returns empty, no crash
        return Submission.objects.filter(student=linked.student)
```

This way, if the link doesn't exist, the app returns zero submissions instead of crashing.

---

### Risk #3: No Audit Logging

**What's wrong:**
There's no record of who accessed what submission or when. In a real classroom system, you need to log all access for compliance and to detect suspicious activity (e.g., an instructor accessing a student's submission at 3 AM when they shouldn't).

**Production fix:**

- Add an `AuditLog` model that records all read/write actions
- Log: User, Action (create/read/update/delete), Resource, Timestamp, IP address
- Monitor for anomalies (e.g., same user accessing submissions from 10 different countries simultaneously)

---

## 🚢 Deployment

## 📚 How to Navigate This Submission

This submission has two main parts:

### Part 1: Demo Application (This Backend)

Everything in the root directory. To understand the implementation:

1. **Start with:** `accounts/models.py` — see the User and ObserverStudentLink models
2. **Then:** `accounts/permissions.py` — understand role-based checks
3. **Then:** `submissions/views.py` and `assignments/views.py` — see how `get_queryset()` enforces row-level permissions
4. **Teaching comment:** `accounts/management/commands/seed.py`

Run the app locally using [Local Setup](#-local-setup) section above.

### Part 2: Teaching Package

Located in `teaching-package/` directory. These are the materials you would give learners:

1. **`01-session-outline.md`** — 60-minute lesson plan
2. **`02-learning-objectives.md`** — What learners will be able to do
3. **`03-concept-explainers.md`** — Deep dives on JWT, RBAC, row-level permissions with diagrams
4. **`04-anticipated-misconceptions.md`** — Common confusions and how to correct them
