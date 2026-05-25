# Concept Explainers

**Session:** Authentication & Role-Based Access Control in Django
**Audience:** Django learners who have built basic views and a first DRF API. No prior experience with authentication or access control.

---

## 1. Authentication vs. Authorization

These two words are used interchangeably in casual conversation. In security they mean completely different things, and mixing them up leads to real vulnerabilities.

**Authentication** is the process of proving identity.
**Authorization** is the process of deciding what that identity is allowed to do.

A useful analogy: think of a hospital.

- You show your staff ID at the entrance. The security guard checks it and confirms you work there. That is **authentication** — the hospital now knows *who* you are.
- You walk to the pharmacy. The pharmacist checks your role before dispensing controlled medication. Not everyone who works at the hospital can collect those drugs. That is **authorization** — the system is deciding *what* you can do.

In a Django API, these are two separate layers:

| Layer | Question answered | Where it lives in DRF |
|-------|-------------------|----------------------|
| Authentication | Who is making this request? | `authentication_classes`, JWT middleware |
| Authorization | Is this user allowed to do this? | `permission_classes` |

**Critical insight:** Authentication happens once per request, during token validation. Authorization happens at every view, every time. You can have authentication without meaningful authorization (everyone who logs in can do everything) or you can try to have authorization without authentication (you check roles, but you never verified the user is who they claim to be — this is always broken).

In our classroom API:
- The JWT token handles authentication — it proves the request comes from a specific user
- The permission classes handle authorization — they decide whether that user can hit a given endpoint

---

## 2. How JWTs Work

### The problem JWTs solve

Traditional web applications use **sessions**: when you log in, the server creates a record in its database (or memory) that says "user 42 is currently logged in," and gives you a cookie containing a session ID. Every request sends that cookie, the server looks up the ID, and retrieves the session.

This works fine for a single server serving a browser. It breaks down for APIs because:

- Mobile apps and third-party clients do not use cookies naturally
- If you run multiple servers (horizontal scaling), each server would need access to the same session store
- Cross-domain requests (your React frontend on one domain hitting your API on another) make cookies complicated

**JWTs are stateless.** The server does not store anything. The token itself contains all the information the server needs, and the server can verify it cryptographically without a database lookup.

### Anatomy of a JWT

A JWT looks like this:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTcxNzA3MDAwMH0.4XkY2mN9Rp1sVqT8uZwE3aLcBdOeHfMjKnPvYrWxQs
```

That is three Base64-encoded strings joined by dots. The three parts are:

**Header** — describes the token type and signing algorithm:
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload** — contains the *claims*: facts about the user that the server embedded when it issued the token:
```json
{
  "user_id": 3,
  "role": "student",
  "exp": 1717070000
}
```

**Signature** — a cryptographic hash of the header and payload, created using a secret key only the server knows.

### ⚠️ The most important thing learners get wrong about JWTs

**The payload is not encrypted. Anyone can read it.**

Go to [jwt.io](https://jwt.io) right now, paste any JWT, and you will see the decoded payload in plain text. Base64 encoding is not encryption — it is just a way to represent binary data as text.

What makes a JWT secure is the **signature**. When the server receives a token, it recomputes the signature using its secret key and compares it to the signature in the token. If someone modified the payload (for example, changed `"role": "student"` to `"role": "instructor"`), the signature would no longer match and the token would be rejected.

The conclusion: **never put sensitive data in a JWT payload** (no passwords, no payment info). Only put data you are comfortable with anyone seeing.

### Access tokens vs. refresh tokens

SimpleJWT issues two tokens on login:

| Token | Typical lifetime | Purpose |
|-------|-----------------|---------|
| Access token | 5–60 minutes | Sent with every API request in the `Authorization` header |
| Refresh token | 1–30 days | Used only to obtain a new access token when the current one expires |

Why two tokens? A short-lived access token limits damage if it is stolen: an attacker who intercepts it can only use it for a few minutes. The refresh token is stored securely (in an HttpOnly cookie, or in a secure app store) and is only sent to one endpoint. This gives you security (short-lived access) without making the user log in every 15 minutes.

### The request flow in our app

```
1. Client  →  POST /api/v1/auth/login/   (email + password)
2. Server  →  validates credentials
           →  issues access_token (15 min) + refresh_token (7 days)
3. Client  →  GET /api/v1/assignments/
              Authorization: Bearer <access_token>
4. Server  →  validates signature on access_token
           →  sets request.user from token payload
           →  runs permission checks
           →  returns data
5. (access token expires)
6. Client  →  POST /api/v1/auth/refresh/   (refresh_token)
7. Server  →  issues new access_token
```

In Django, step 4 is handled by `JWTAuthentication` from SimpleJWT, configured in `DEFAULT_AUTHENTICATION_CLASSES`. By the time your view runs, `request.user` is already populated — you do not need to decode the token yourself.

---

## 3. Role-Based Access Control with DRF Permission Classes

### What RBAC is

Role-Based Access Control (RBAC) is an authorization model where permissions are attached to *roles*, and users are assigned roles. Instead of deciding per-user what each person can do, you define capability sets (roles) and assign users to them.

In our classroom system:

| Role | What they can do |
|------|-----------------|
| `INSTRUCTOR` | Create assignments, view all submissions for their classes, leave feedback |
| `STUDENT` | View enrolled assignments, submit work, view their own feedback |
| `OBSERVER` | Read-only view of one specific student's progress |

### How DRF permission classes work

Every DRF view has a `permission_classes` attribute — a list of classes that are checked before the view logic runs. If any permission class returns `False`, DRF stops and returns a 403 Forbidden response.

A permission class is a Python class that inherits from `BasePermission` and overrides one or both of these methods:

```python
class BasePermission:
    def has_permission(self, request, view) -> bool:
        # Called before the view runs.
        # Checks role, authentication status, HTTP method, etc.
        # Return True to allow, False to deny.

    def has_object_permission(self, request, view, obj) -> bool:
        # Called when a specific object is being accessed (retrieve, update, destroy).
        # Receives the actual database object being requested.
        # Return True to allow, False to deny.
```

Here is the `IsInstructor` class from our app:

```python
# permissions.py

class IsInstructor(BasePermission):
    # TEACHING NOTE: We check is_authenticated first for a specific reason.
    # An unauthenticated user has request.user set to AnonymousUser,
    # which has no `role` attribute. Accessing .role on it would raise
    # an AttributeError. The `and` operator short-circuits: if is_authenticated
    # is False, Python never evaluates the right side, so we never hit the error.
    # This pattern — check auth before checking role — is standard across the codebase.
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == UserRole.INSTRUCTOR
        )
```

Attaching it to a view:

```python
class AssignmentViewSet(ModelViewSet):
    permission_classes = [IsInstructor]  # only instructors reach the view logic
```

### The role check answers "what kind of user are you?"

Role-level permission is a binary gate. Either you are an instructor or you are not. Either you can create assignments or you cannot. This is appropriate for controlling which *endpoints* a role can access.

But role-level permission says nothing about *which rows* a user can see. Two students both have the `STUDENT` role. Without additional filtering, both students would see every submission in the database. That is the next layer.

---

## 4. Row-Level Security: The Layer Most Systems Miss

### The problem

Imagine two students, Alice (id=1) and Bob (id=2). Both are authenticated. Both have the `STUDENT` role, so they both pass the `IsStudent` permission check on `GET /api/v1/submissions/`.

Without row-level filtering:

```python
# Dangerous — returns everything
def get_queryset(self):
    return Submission.objects.all()
```

Alice calls `GET /api/v1/submissions/` and gets back all submissions from every student in the system. She can also try `GET /api/v1/submissions/2/` and read Bob's work directly. This is a real vulnerability class called **Insecure Direct Object Reference (IDOR)** — the API lets users reference objects they should not have access to.

Role-based permissions at the endpoint level did not prevent this. The problem is that RBAC answers "can this type of user access this endpoint?" but not "can this specific user access this specific row?"

### Queryset filtering

The fix is to scope every query to the requesting user:

```python
def get_queryset(self):
    user = self.request.user

    if user.role == UserRole.STUDENT:
        # Only return this student's own submissions
        return Submission.objects.filter(student=user)

    if user.role == UserRole.INSTRUCTOR:
        # Only return submissions for this instructor's assignments
        return Submission.objects.filter(assignment__instructor=user)

    if user.role == UserRole.OBSERVER:
        # Only return submissions for the specific student this observer is linked to
        linked_student = user.observer_profile.linked_student
        return Submission.objects.filter(student=linked_student)

    return Submission.objects.none()  # deny by default
```

Now Alice calls `GET /api/v1/submissions/` and gets only her rows. If she tries `GET /api/v1/submissions/2/` (Bob's submission), DRF calls `get_queryset` first to scope the query, finds no matching row for her, and returns **404 Not Found** — not 403.

### Why 404 and not 403?

A 403 response says: "This resource exists, and you do not have permission to see it." That confirms to the attacker that the resource exists and is worth targeting. A 404 response reveals nothing. This is called **security through non-disclosure of existence** — a standard practice for protecting sensitive records.

### The Observer: a worked example of row-level logic

The Observer role illustrates why row-level permissions cannot be replaced by role-level permissions.

Consider two observers: Parent A (linked to Student Alice) and Parent B (linked to Student Bob). Both users have `role == OBSERVER`. If we checked only the role, both parents would see all observer-accessible data — which would include each other's children. That is obviously wrong.

The correct check is relational: does this observer have a relationship record linking them to the student whose data is being requested?

```python
# In ObserverProfile model:
class ObserverProfile(models.Model):
    observer = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='observer_profile'
    )
    linked_student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='observers'
    )
```

```python
# In the view's get_queryset:
if user.role == UserRole.OBSERVER:
    linked_student = user.observer_profile.linked_student
    return Submission.objects.filter(student=linked_student)
```

The logic is: "I do not care what role you have. I care whether *you specifically* are linked to *this specific student*." That is row-level security — access control that depends on a relationship between the requesting user and the data row, not on a role category.

### The four layers, summarized

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Authentication                                     │
│  "Is the request coming from a verified user?"               │
│  Tool: JWT middleware, JWTAuthentication                     │
│  Lives in: settings.py → DEFAULT_AUTHENTICATION_CLASSES      │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Role-Level Authorization                           │
│  "Does this role have permission to use this endpoint?"      │
│  Tool: Custom BasePermission subclasses                      │
│  Lives in: permissions.py, view.permission_classes           │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Row-Level Authorization                            │
│  "Which specific rows is this user allowed to see?"          │
│  Tool: get_queryset filtering, has_object_permission         │
│  Lives in: viewsets.py → get_queryset                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Data Integrity                                     │
│  "Can the client manipulate ownership fields on write?"      │
│  Tool: perform_create override, serializer field exclusions  │
│  Lives in: viewsets.py → perform_create                      │
└─────────────────────────────────────────────────────────────┘
```

Each layer handles a different question. Skipping any one of them leaves a gap that the others cannot fill.