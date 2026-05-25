# Anticipated Misconceptions

**Session:** Authentication & Role-Based Access Control in Django
**Audience:** Learners with basic DRF experience, no prior authentication or access control background.

---

## Framing Note

Every misconception listed here is *reasonable*. Learners arrive at these beliefs because the concepts were partially explained elsewhere, or because an analogy they used earlier (correctly) broke down in a new context. The goal when correcting a misconception is not to make the learner feel they were wrong — it is to show them exactly where their mental model stopped being accurate, and extend it.

---

## Misconception 1: "If I add authentication, my API is secure"

### The misconception

A learner who has just successfully implemented JWT login believes the work is done. They have a login endpoint, the API requires a Bearer token, unauthenticated requests get a 401 — it feels complete.

### Why learners naturally arrive here

Authentication is the most visible security feature. It is the front door. Learners can see it working: no token, no access. This feels like a complete solution because in everyday experience, getting past a locked door means you are allowed to be somewhere.

The curriculum also tends to cover authentication before permissions and before queryset filtering. Learners who have not yet seen the next layers reasonably assume authentication *is* the security layer.

### What is actually true

Authentication establishes *identity*. By itself, it says nothing about what that identity can do, or which rows of data it can see. A fully authenticated user with a valid JWT can still:

- Access endpoints intended for a different role
- Read another user's records by guessing their ID
- Submit data that claims to belong to someone else

Authentication answers "who are you?" The other two questions — "what are you allowed to do?" and "which rows are yours?" — require authorization and queryset filtering respectively.

### How to correct it without making the learner feel foolish

Do not say "authentication is not enough." Instead, demonstrate the gap:

1. Have learners log in as a student and obtain a valid token — authentication working correctly
2. Now ask: "You are authenticated. Let's see what you can access." Call `GET /api/v1/submissions/` without any queryset filtering
3. Show that the authenticated student can see every submission in the database — including other students' work

The learner's mental model was not wrong, it was incomplete. Say:

> "Authentication did exactly what it promised — it confirmed who you are. The gap is that we haven't yet told the system what you're allowed to *do* or *see*. Those are separate problems."

---

## Misconception 2: "Role checks are sufficient — I don't need to filter querysets"

### The misconception

A learner who has implemented role-based permissions believes that protecting endpoints by role is the complete authorization solution. Students cannot hit instructor endpoints. Instructors cannot hit observer endpoints. The roles are enforced. What else is there?

### Why learners naturally arrive here

RBAC is typically taught as the authorization solution. The phrase "role-based access control" itself implies that roles *control access* — which they do, at the endpoint level. Learners extend this correctly-understood concept one step further than it applies.

It also feels logically complete: if only students can access the submissions endpoint, and each student is a different person, why would they see each other's data? The role *feels* like a sufficient discriminator because roles are per-person. What the learner is missing is that two different people can have the same role.

### What is actually true

Roles define what *types* of users can access what *types* of endpoints. They do not define which *rows* a specific user within that type can access.

Two students both pass `IsStudent`. Without queryset filtering, `Submission.objects.all()` returns all 200 submissions from all 50 students. The role check let both of them through the door — it said nothing about which filing cabinet they can open once inside.

This is the distinction between:
- **Endpoint-level authorization** (can this role access this URL?) — handled by permission classes
- **Data-level authorization** (can this user access this specific row?) — handled by queryset filtering

### How to correct it without making the learner feel foolish

The IDOR demonstration is the most effective correction. Do not describe it — show it:

1. Log in as Student A (id=1)
2. Call `GET /api/v1/submissions/` — without row-level filtering, all submissions are visible
3. Call `GET /api/v1/submissions/5/` — Student B's submission, returned in full

Then ask: "The role check passed. Was this a security failure?" The learner will recognize it was. Then show the queryset fix and rerun the same requests. The 404 on step 3 lands with weight because they just saw the vulnerability themselves.

> "Role-based permissions are the right tool for endpoint-level access. Queryset filtering is the right tool for data-level access. They answer different questions — you need both."

---

## Misconception 3: "JWTs are encrypted — I can store sensitive data in them"

### The misconception

Because JWTs look like a long, unreadable string of random characters, learners assume the content is encrypted and therefore private. Some learners go further and plan to store sensitive information — user emails, permission lists, even payment flags — in the token payload because it "travels securely."

### Why learners naturally arrive here

The visual appearance of a JWT is indistinguishable from an encrypted string. Both look like `eyJhb...`. Learners are also often told JWTs are "secure" — which is true, but in a specific and limited sense. The string "secure" carries a connotation of privacy that does not apply here.

Additionally, learners coming from session-based authentication know that session data is stored server-side and is private. They may incorrectly map this mental model to JWTs, assuming the token somehow protects the data it contains.

### What is actually true

JWTs are **signed**, not **encrypted**. Signing ensures integrity (the payload has not been tampered with) but not confidentiality (the payload is readable by anyone).

The three parts of a JWT are Base64-encoded — a reversible encoding, not encryption. Any person or system that receives the token can decode the header and payload instantly. The signature prevents modification; it does not prevent reading.

### How to correct it without making the learner feel foolish

The live decoding exercise is the most effective demonstration. During the session:

1. Log in and copy the returned access token
2. Go to [jwt.io](https://jwt.io) in the browser — no login, no key, no tool
3. Paste the token
4. The payload is displayed immediately in plain text

Watch the room. Most learners will be surprised. That reaction is the lesson.

> "The token is tamper-proof — the signature prevents anyone from editing it and re-signing it without the server's secret key. But it is not private. Think of it like a sealed envelope that is made of glass: you cannot change what's inside, but you can absolutely read it."

Follow up: explain what *should* go in a JWT payload — only identifiers and short-lived claims like `user_id`, `role`, and `exp`. Never passwords, PII, or any value that would cause harm if read by a third party.

---

## Misconception 4: "The frontend handles access control — the backend just needs to serve data"

### The misconception

Learners who have built frontends before sometimes arrive with the belief that role-based access is a UI problem: hide the admin panel from non-admin users, don't show the submit button to observers. If the button isn't there, the request can't be made.

### Why learners naturally arrive here

This misconception is grounded in real experience. Frontend role-gating works in practice for everyday users — a student who does not see a "Create Assignment" button will not try to create an assignment. The mental model is not irrational; it describes what most users will actually do.

The gap is that it assumes users interact exclusively through the intended UI, and that they are not adversarial.

### What is actually true

Any HTTP request that a browser can make, Postman can make. Any request that Postman can make, a curl command can make. The frontend is completely bypassed the moment someone opens developer tools or an API client.

A learner who relies on frontend access control and ships no backend permissions has not built a secure system — they have built a system that is secure against users who do not know how HTTP works.

### How to correct it without making the learner feel foolish

Demonstrate it rather than assert it. During the session:

1. Show the working frontend (or a hypothetical): the student role does not see an "Add Assignment" button
2. Open Postman
3. Call `POST /api/v1/assignments/` directly with the student's token — without the button, without the UI
4. If the backend has no permission check, it succeeds

> "The frontend is a courtesy for legitimate users. It is not a security boundary. Security boundaries live in the backend, because the backend is the only part of the system you control. Anyone can talk to your API — your job is to make sure the API handles that correctly, regardless of what tool they're using."

This framing validates the frontend work (it is still correct and necessary for UX) while clarifying that it operates at a different layer with a different purpose.