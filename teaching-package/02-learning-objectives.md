# Learning Objectives

**Session:** Authentication & Role-Based Access Control in Django
**Duration:** 60 minutes

---

## Overview

These objectives are written for learners who have built basic Django views and a first DRF API but have never implemented authentication or access control. Each objective is specific and observable — it describes something a learner can *do* or *demonstrate*, not something they passively "understand."

---

## Objective 1 — Implement JWT Login and Token Refresh

**Statement:** Given a Django project with SimpleJWT installed, the learner can implement a login endpoint that returns an access token and a refresh token, and demonstrate end-to-end token refresh using Postman.

**Why this matters:** Token management is the foundation everything else sits on. A learner who cannot reliably produce and refresh a token cannot test any of the permission logic that follows.

**How it will be assessed:**

- Learner successfully calls `POST /api/v1/auth/login/` and receives a JSON response containing both `access` and `refresh` fields
- Learner calls `POST /api/v1/auth/refresh/` with the refresh token and receives a new access token
- Learner can decode the access token on jwt.io and identify the `user_id` and `role` fields in the payload
- Learner can explain verbally why access tokens expire quickly while refresh tokens are longer-lived

---

## Objective 2 — Write a Custom DRF Permission Class That Enforces Role Boundaries

**Statement:** The learner can write a `BasePermission` subclass that restricts an endpoint to a specific role, and verify the restriction produces a 403 response for users with a different role.

**Why this matters:** DRF ships with `IsAuthenticated` and `IsAdminUser`. Real systems need fine-grained role logic. This objective bridges "I have heard of permissions" to "I can write one."

**How it will be assessed:**

- Learner writes a permission class that correctly overrides `has_permission` and checks `request.user.role`
- Learner attaches the class to a view using `permission_classes`
- Authenticated student receives 403 on an instructor-only endpoint
- Learner can explain why the check uses `is_authenticated and role ==` rather than `role ==` alone (unauthenticated users have `AnonymousUser`, which has no `role` attribute)

---

## Objective 3 — Implement Row-Level Security Using Queryset Filtering

**Statement:** The learner can override `get_queryset` in a `ModelViewSet` to return only the rows the requesting user is authorised to see, and demonstrate that a user cannot retrieve another user's records even by guessing a numeric ID.

**Why this matters:** This is the most commonly missed layer in student-built APIs. Passing Objective 2 without Objective 3 produces an API where roles are enforced at the door but all data is visible once you're inside.

**How it will be assessed:**

- `GET /api/v1/submissions/` returns only the authenticated student's submissions — not all submissions in the database
- `GET /api/v1/submissions/{other_user_id}/` returns 404, not 403 (the system does not confirm the row exists)
- Learner can explain in their own words why returning 404 is preferable to 403 for hidden rows

---

## Objective 4 — Prevent Client-Side Ownership Spoofing During Data Creation

**Statement:** The learner can modify a DRF serializer or `perform_create` method so that the ownership field (e.g., `student`) is always set server-side from `request.user`, and verify that passing a different user's ID in the request body has no effect.

**Why this matters:** A student who can POST `{"student": 99, "content": "..."}` and have that accepted has effectively submitted work on behalf of another user. This is a straightforward attack that a single line of server-side code prevents.

**How it will be assessed:**

- Learner calls `POST /api/v1/submissions/` with a body containing `"student": <another_user_id>` — the created record uses `request.user` as the student, ignoring the body value
- Learner locates the `perform_create` override (or `validated_data.pop`) in the codebase and explains what it does
- Learner can explain the general principle: never trust the client to tell you who owns the data

---

## Objective 5 — Distinguish Authentication, Role-Level Authorization, and Row-Level Authorization

**Statement:** The learner can explain — without referring to notes — the difference between the three security layers, describe where each is enforced in the codebase, and give an example of a vulnerability that exists when each layer is missing.

**Why this matters:** Learners who conflate these layers will apply the wrong tool to the wrong problem. A learner who only knows "use permissions" will write role checks where queryset filters are needed, and vice versa.

**How it will be assessed:**

- Given three code snippets (one from `authentication.py`, one from `permissions.py`, one from `get_queryset`), learner correctly identifies which layer each represents and what would break if it were removed
- Learner can describe the Observer scenario — same role as other observers, different data access — and explain why a role check alone is insufficient
- Verbal or written answer uses the terms *authentication*, *authorization*, and *data scoping* correctly and without prompting