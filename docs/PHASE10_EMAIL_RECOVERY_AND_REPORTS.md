# EduMind AI — Phase 10 email delivery, reports, and account recovery

These updates were developed **after the September–October 2026 research study**. They are not claimed as features that all 87 research participants used.

## Added features

1. Student dashboard → Progress Tracking → **Email my progress report**. Delivery is limited to the signed-in student's saved email.
2. Lecturer report → **Email this report to me**, available only when the Student has granted both report visibility and **separate email permission**. Delivery is limited to the Lecturer's registered email. Revoking the grant also removes permission.
3. Login and registration forms have password Show/Hide controls.
4. Forgot Password sends a single-use password reset URL valid for 30 minutes. Tokens are random, stored only as SHA-256 digests, and limited to three requests/hour per address and 30/hour per source IP. Resets require 12–128 character passwords; old sessions are invalidated when the password hash changes.

Report emails contain only task counts, recent activity and a clearly labelled behavioural indicator. They exclude chats, attachments, individual questionnaire answers and comments. No arbitrary recipient field is supported.

## Apply to your local project (BEFORE live deployment)

1. Make a secure, tested backup of the existing Aiven MySQL database and protect the consent/research records.
2. Check out the feature branch:
   `git fetch origin`
   `git switch feature/secure-email-reports-recovery`
   (If local changes exist, commit or stash them first.)
3. Configure email variables in a local `.env`. **Do not commit secrets**. Example using Brevo:
   `APP_PUBLIC_URL=https://edumind-ai-project.alwaysdata.net`
   `EMAIL_BACKEND=brevo`
   `EMAIL_FROM=verified-sender@example.com`
   `BREVO_API_KEY=put-your-private-key-here`

   Register a sender/domain with the email provider and verify it. Sending is disabled until valid configuration is supplied. Alternative encrypted SMTP:
   `EMAIL_BACKEND=smtp`
   `EMAIL_FROM=verified-sender@example.com`
   `SMTP_HOST=your-provider-host`
   `SMTP_PORT=587`
   `SMTP_USER=your-provider-user`
   `SMTP_PASSWORD=your-provider-app-password`
   `SMTP_USE_STARTTLS=true`
   `SMTP_USE_SSL=false`
   Use SMTP over TLS; never send unencrypted credentials.
4. In **MySQL Workbench**, choose the correct existing database and verify using `SELECT DATABASE();`. Run `database/email_features_phase10.sql` only after the backup. This adds one new table, `email_action_events`, and the nullable-safe/default-false email permission column `lecturer_access_grants.email_allowed`. There are no DROP/TRUNCATE/DELETE operations; existing `evaluation_responses` and `evaluation_item_responses` are not modified.
5. Test locally with `python -m pytest tests -q`. The test client sends emails to an in-memory outbox, never to real addresses.
6. Use two private test mailboxes to exercise real provider delivery on local or staging HTTPS: Student report, Lecturer report after explicit consent, reset link, 30-minute expiration, consumed-link denial, wrong password, access revocation.
7. Only after all checks pass: merge the pull request, update alwaysdata's environment variables, apply the SQL migration to the correct production DB, deploy from GitHub via your documented `git pull` and restart WSGI. Check server error logs and audit the real send.
8. If mail delivery fails, leave existing passwords and research data intact. Do not reset users or rebuild tables.

**Rollout note:** The first login after this update may require signing in again. Authentication sessions now bind to the current password hash, which invalidates previous sessions when a password is reset.

## Data stewardship / scope

- Never send individual study answers or identifying consent records by email.
- Student-to-Lecturer report emails require their own explicit, revocable grant checkbox.
- The backend determines the destination from the authenticated account; it never accepts a user-supplied destination.
- Existing Aiven study data and the original SPSS dataset should remain unchanged.
- New system features are post-study improvements, so don't attribute them to earlier participant responses.

## Dissertation change-log section

Under **Chapter 6 — Implementation**, add a subsection titled **Enhancements Following Supervisor Feedback**. Record the password visibility control, reset workflow, secure email API integration, optional lecturer email permission, new `email_action_events` table and testing results.

In Chapter 7, include the GitHub Actions regression run, plus live email-delivery and expired-token checks after performing them. Use Appendix F for screenshots of the new UI and redacted emails, and place the three normal-curve SPSS histograms in Appendix E. Preserve the formal **Declaration of Originality** as a separate front-matter item; it should not be replaced by a software change log.
