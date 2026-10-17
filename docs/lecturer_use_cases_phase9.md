# Dissertation update — Chapter 5 / UML Actors

**System boundary:** EduMind AI Learning Assistant.

1. **Student** — primary, internal human actor: register, sign in, manage tasks, view dashboard/progress, converse with AI, request personalised feedback, complete evaluation, **grant/revoke lecturer report access**.
2. **Lecturer** — secondary, internal human actor: sign in using an operator-created account, view **only consenting students'** read-only progress reports, see behavioural indicators, view draft questionnaire **construct means**; sign out.
3. **Groq AI Service** — external supporting system actor: receives chatbot generation requests from the Flask backend and returns model-generated academic support responses. A Groq service is not a third human user role.

**Use case diagram:** Draw the three actors outside the EduMind system boundary. Student associations: `Manage Study Tasks`, `View Dashboard`, `View Progress`, `Use AI Study Coach`, `Receive Feedback`, `Complete Evaluation`, `Grant Report Access`, `Revoke Report Access`. Lecturer associations: `Authenticate as Lecturer`, `View Authorised Students`, `View Student Progress Report`, `View Summary Evaluation Indicators`. The Groq actor associates with `Generate AI Response`, invoked by `Use AI Study Coach`.

**Requirements (new):**
- FR23 Student can grant an existing lecturer scoped read-only access to named progress and aggregate evaluation information.
- FR24 Student can revoke that access at any time.
- FR25 Lecturer role can be created only by an authorised local operator, not public registration.
- FR26 Lecturer can view report information only for a student with an active grant.
- FR27 Lecturer cannot view chatbot messages, uploaded documents, evaluation comments or individual survey item answers.
- FR28 Lecturer's dashboard and reports do not mutate task status or motivation score records.
- NFR13 Role and ownership checks are server-side, and grant/revoke actions require CSRF-protected POST requests.

**Implementation:** `users.role` and `lecturer_access_grants` are introduced by a backwards-compatible migration. Separate lecturer routes enforce `lecturer_only`; legacy student modules redirect authenticated lecturers to their reporting area. Student grant/revoke endpoints use ownership checks and server-side validation. Reporting performs read-only calculations and uses only the most recent draft v2 matched questionnaire summary.

**Ethical limit:** These permissions do not replace institutional research ethics approval or participant informed consent. Project-written questionnaire items and behavioural indicators are not validated psychological diagnostic scales. Data-sharing permissions must be explained to each student.

**Testing evidence:** Run `tests/test_lecturer_phase9.py` and document 2-account and 3-account manual access checks, revocation, cross-account URL access (404), and preservation of prior student workflows. Do not claim completion until the live MySQL app and test suite pass.
