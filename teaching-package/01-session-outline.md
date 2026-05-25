# Session Outline — Authentication & Role-Based Access Control in Django

**Module:** Final Django Module — Session 4 of 4
**Duration:** 60 minutes
**Format:** Live coding + Postman demos + concept discussion
**Prerequisites:** Learners have built basic Django views and created their first DRF API. No prior experience with authentication or permissions.

---

## The 60-Minute Plan

| Time | Segment | Format |
|------|---------|--------|
| 0–5 min | Context: why access control matters | Discussion |
| 5–20 min | Authentication — proving who you are | Live demo + explanation |
| 20–35 min | Role-based access control | Live demo + code walkthrough |
| 35–50 min | Row-level security — the part most systems miss | Live demo + code walkthrough |
| 50–57 min | Guided practice | Learner activity |
| 57–60 min | Recap and Q&A | Discussion |

---

## Segment Detail

### 0–5 min — Context Setting

Open with a concrete scenario rather than definitions:

> "You have built an API for a school. A student logs in and requests `/api/submissions/`. Should they see *every* student's work, or only their own? What stops them from changing the URL to `/api/submissions/2/` and reading someone else's assignment?"

Take one or two answers from the room. The goal is to surface the gap: learners have been building APIs that trust the caller completely. Today we stop trusting callers.

Show the live demo briefly — just enough for learners to see the finished system. A student logging in, getting a token, and being blocked from an instructor endpoint. Don't explain it yet. The goal is curiosity, not comprehension.

**Why this first:** People learn better when they know why the lesson matters before the mechanics arrive. Starting with the demo gives learners a destination to orient toward.

---

### 5–20 min — Authentication: Proving Who You Are

**Core question for this segment:** "How does the server know *who* is making this request?"

**Live demo sequence (Postman):**

1. `POST /api/v1/auth/login/` with `student@demo.dev` credentials → show the response containing `access` and `refresh` tokens
2. Copy the access token, paste it into jwt.io in the browser — show the decoded payload live. Point out: the payload is readable. It is *not* encrypted.
3. Make a request to `GET /api/v1/assignments/` *without* a token — show the 401
4. Add the `Authorization: Bearer <token>` header — show the 200
5. Demonstrate token refresh: `POST /api/v1/auth/refresh/` with the refresh token → new access token

**Concepts to cover:**

- Authentication vs. authorization — establish these terms clearly before moving on. Authentication is identity. Authorization is permission. They are different problems solved at different layers.
- What a JWT contains (header, payload, signature) and why the signature matters
- Why access tokens are short-lived and refresh tokens exist
- Why APIs use tokens instead of sessions (statelessness, mobile clients, cross-domain requests)

**Why this segment comes before permissions:** You cannot meaningfully discuss what a user is allowed to do until the system knows who the user is. `request.user` must exist before any permission check can run.

---

### 20–35 min — Role-Based Access Control

**Core question for this segment:** "Given that we know *who* the user is, how do we decide what they're *allowed* to do?"

**Live demo sequence:**

1. Log in as `student@demo.dev`. Attempt `POST /api/v1/assignments/` — show the 403 Forbidden response
2. Log in as `instructor@demo.dev`. Make the same request — show it succeeds
3. Open `permissions.py` in the codebase. Walk through `IsInstructor` class line by line

**Code to walk through:**

```python
class IsInstructor(BasePermission):
    """
    Grants access only to users with the INSTRUCTOR role.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == UserRole.INSTRUCTOR
        )
```

**Key teaching points:**

- `has_permission` runs on every request before the view executes — it is a gatekeeper, not a filter
- Returning `False` produces a 403, not a 404. Discuss briefly why (the distinction matters for security vs. UX)
- Roles are "capability buckets": the role answers what *kind* of user you are, not which specific data you can touch. That is the next segment.

**Why this segment follows authentication:** Role checks require a known user. Only once the JWT middleware has set `request.user` can a permission class inspect `request.user.role`.

---

### 35–50 min — Row-Level Security: The Part Most Systems Miss

**Core question for this segment:** "Even if a user has the right role, how do we ensure they can only see *their own* data?"

**Open with the attack:**

> "Our student is authenticated. They have the Student role. So they can hit `GET /api/v1/submissions/`. But what if the database has 200 submissions from 50 students? What does the student actually get back?"

Show — without row-level filtering — that a naive implementation returns all 200 rows. This is a real class of vulnerability called an Insecure Direct Object Reference (IDOR).

**Live demo sequence:**

1. Logged in as `student@demo.dev` — `GET /api/v1/submissions/` returns only their own three submissions
2. Attempt `GET /api/v1/submissions/99/` (a submission belonging to another student) — show the 404
3. Log in as `observer@demo.dev` — `GET /api/v1/submissions/{id}/feedback/` returns only the linked student's data. Explain the Observer is *linked* to a specific student record — it is not a role check, it is a relationship check.

**Code to walk through:**

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

**Key teaching points:**

- Queryset filtering happens at the data layer, not the permission layer — these are different tools for different problems
- Return 404 (not 403) when a row exists but the user shouldn't see it — never confirm existence of data the user can't access
- The Observer is the worked example of row-level: two observers with the same role could be linked to different students. Role alone cannot enforce this. Only a relationship check can.

**Why this is the core segment:** This is the layer that production systems most commonly get wrong. Learners who leave understanding only role-level protection will write vulnerable APIs. This segment is the reason the lesson exists.

---

### 50–57 min — Guided Practice

Learners work individually or in pairs. Two tasks, in order of difficulty:

**Task 1 (accessible):** Using the seeded demo credentials, use Postman to:
- Log in as each of the three roles
- Identify one endpoint each role can access and one it cannot
- Attempt to access another student's submission as the student — record the response code and explain why

**Task 2 (stretch):** In the codebase, find the `get_queryset` method for `SubmissionViewSet`. Modify it to add a fourth hypothetical role — `AUDITOR` — that can see all submissions but cannot create or modify anything.

**Why practice before the recap:** Active retrieval during a session embeds the concepts more effectively than hearing a summary. The tasks are designed to be completable in 7 minutes — they consolidate, not introduce.

---

### 57–60 min — Recap and Q&A

Verbal recap — ask the room, do not tell:

- "What is the difference between a 401 and a 403?" (authentication failure vs. authorisation failure)
- "Why does the Observer need a row-level check rather than just a role check?"
- "Where in the code does `request.user` get set? What sets it?"

Close with a one-sentence mental model:

> **Authentication answers WHO. Authorization answers WHAT. Queryset filtering answers WHICH ROWS.**

Take any remaining questions.