# Session Outline — Authentication & Role-Based Access Control in Django

**Module:** Final Django Module — Session 4 of 4
**Duration:** 60 minutes
**Format:** Live coding + Postman demos + concept discussion
**Prerequisites:** Learners have built basic Django views and created their first DRF API. No prior experience with authentication or permissions.

---

## The 60-Minute Plan

| Time      | Segment                     |
| --------- | --------------------------- |
| 0–5 min   | Hook: the core problem      |
| 5–20 min  | JWT login and token refresh |
| 20–35 min | Role-based permissions      |
| 35–50 min | Row-level security          |
| 50–57 min | Guided practice             |
| 57–60 min | Recap and Q&A               |

---

## Segment Detail

### 0–5 min — Hook

**Open with the problem, not definitions:**

> "You've built an API for a school. A student logs in and requests `/api/submissions/`. Should they see every student's work, or only their own? What stops them from changing the URL to `/api/submissions/2/` and reading someone else's assignment?"

Let them answer. The gap I'm surfacing: all the APIs they've built so far trust the caller completely. This session is about not doing that.

Quick demo of the finished system — student logs in, gets a token, hits an endpoint they shouldn't be able to reach, gets blocked. Enough to make them curious. Don't explain yet.

---

### 5–20 min — Authentication: JWT Login and Token Refresh

**Postman demo sequence:**

1. `POST /api/v1/auth/login/` with `student@demo.dev` — show the response with `access` and `refresh` tokens
2. Copy the access token, paste into jwt.io — decode it live to show the payload (readable, not encrypted)
3. `GET /api/v1/assignments/` without a token → 401
4. Same request with `Authorization: Bearer <token>` → 200
5. `POST /api/v1/auth/refresh/` with the refresh token → new access token

**Concepts to land:**

- Auth vs. authz — they're different problems
- JWT structure: header, payload, signature. Payload is readable, signature prevents tampering.
- Why access tokens are short-lived and refresh tokens are longer
- Why APIs use tokens instead of sessions

The reason this comes first: can't talk meaningfully about what a user can do until the system knows who they are. `request.user` has to exist first.

---

### 20–35 min — Role-Based Permissions

**Demo sequence:**

1. Log in as `student@demo.dev`, try `POST /api/v1/assignments/` → 403 Forbidden
2. Log in as `instructor@demo.dev`, same request → succeeds
3. Open `permissions.py`, walk through `IsInstructor` line by line

**Code to show:**

```python
class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == UserRole.INSTRUCTOR
        )
```

**Key points:**

- `has_permission` is a gatekeeper — runs before the view
- Returns 403, not 404 (tells the user the resource exists but they can't access it)
- Need to check `is_authenticated` first — unauthenticated users have `AnonymousUser`, which has no `role` attribute
- Roles answer "what _type_ of user are you?" — not which specific data you can see

This is endpoint-level access control. The next segment is data-level.

---

### 35–50 min — Row-Level Security

**The problem I'm solving:**

> "Our student is authenticated. They have the Student role. They can hit `GET /api/v1/submissions/`. But if the database has 200 submissions from 50 students, what does the student actually get back? All of them?"

Show what a naive implementation does — returns all rows. This is the IDOR vulnerability.

**Demo sequence:**

1. Logged in as `student@demo.dev` — `GET /api/v1/submissions/` returns only their own submissions
2. Try `GET /api/v1/submissions/99/` (another student's submission) → 404
3. Log in as `observer@demo.dev` — can only see the student they're linked to

**Code to show:**

```python
def get_queryset(self):
    user = self.request.user
    if user.role == UserRole.STUDENT:
        return Submission.objects.filter(student=user)
    if user.role == UserRole.INSTRUCTOR:
        return Submission.objects.filter(assignment__instructor=user)
    if user.role == UserRole.OBSERVER:
        linked_student = user.observer_profile.linked_student
        return Submission.objects.filter(student=linked_student)
```

**Key points:**

- Row filtering happens at the queryset layer, not the permission layer — different tools for different problems
- Return 404 when a row exists but the user can't see it (don't confirm existence of hidden data)
- Observer is the worked example: two observers with the same role, different data access. Role checks can't handle this. Only relationship checks can.

This is the layer most systems get wrong. Both earlier layers can pass and this one still leak data.

---

### 50–57 min — Guided Practice

**Task 1 (foundation):**

- Use Postman to log in as each role
- Find one endpoint each can access and one they can't
- Try to access another student's submission — record the response code

**Task 2 (stretch):**

- Find the `get_queryset` method in `SubmissionViewSet`
- Add support for a hypothetical `AUDITOR` role that can see all submissions but can't modify anything

Seven minutes is tight — these are meant to consolidate, not introduce new material.

---

### 57–60 min — Recap and Q&A

**Ask them, don't tell them:**

- "What's the difference between a 401 and a 403?"
- "Why does the Observer need a row-level check rather than just a role check?"
- "Where in the code does `request.user` get set?"

**Closing line:**

> Authentication answers WHO. Authorization answers WHAT. Queryset filtering answers WHICH ROWS.

Take questions.
