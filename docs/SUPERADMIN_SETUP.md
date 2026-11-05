# EduMind AI — Super Admin setup and deployment

## What's new
- Student Research Evaluation pages use short, participant-facing copy. Existing questionnaire items, data fields, consent workflow, and statistical calculations are unchanged. Ethical approval is **not** claimed by the interface cleanup: maintain approval/consent evidence in project documentation and do not recruit participants without necessary authorization.
- A **Super Admin** can create Admin and Lecturer accounts, view account/role status, and activate or suspend non-superadmin accounts. Student responses, private chats and confidential content are not exposed by the Admin Console.
- An **Admin** can create and activate/suspend Lecturer accounts, but cannot appoint other Admins or Super Admins.
- New staff are assigned random unguessable credentials; a **single-use 30-minute password setup link** is emailed to their address. Admins do not see or choose staff passwords. Audit records use the existing `user_activity_logs` table.
- Existing `users.role` is VARCHAR(16) and already supports the `admin` and `superadmin` values, so **no database schema migration is required**.

## Safe release order
1. Keep the existing Aiven production backup, and confirm the live website is operational.
2. Review the pull request and wait for all tests to pass.
3. Merge to `main`. On alwaysdata, fetch with the existing read-only SSH deploy key and fast-forward as documented below:
   ```bash
   cd ~/apps/EduMindAI-Learning-Assistant
   GIT_SSH_COMMAND="ssh -i ~/.ssh/edumind_deploy -o IdentitiesOnly=yes" git fetch origin
   git status --short
   git merge --ff-only origin/main
   ```
   The untracked production-only `wsgi.py` must remain untouched. Stop on any merge error.
4. Restart the existing Python WSGI site in alwaysdata.
5. **Only then** promote one existing owner-controlled account in the live **Aiven `defaultdb`**, not Local MySQL80. The account must already be active and have a known secure password. Verify by SQL first:
   ```sql
   SELECT user_id, email, role, is_active
   FROM defaultdb.users
   WHERE email = 'THE_EXISTING_OWNER_ACCOUNT_EMAIL';
   ```
   Confirm exactly one expected account row, then substitute its verified ID and email:
   ```sql
   START TRANSACTION;
   UPDATE defaultdb.users
   SET role = 'superadmin'
   WHERE user_id = VERIFIED_OWNER_ID
     AND email = 'THE_EXISTING_OWNER_ACCOUNT_EMAIL'
     AND is_active = 1
     AND role IN ('student', 'lecturer', 'admin');
   SELECT ROW_COUNT() AS accounts_promoted;
   COMMIT;
   ```
   Expect `accounts_promoted = 1`. Stop if it is 0 or anything unexpected. Never grant Super Admin through public registration, never use an unverified email, and do not assign this role to several accounts casually.
6. Sign out and sign in again using that owner's existing account. Open **Admin Console**. Use the form to create an Admin at an email they control; that person receives their own setup link. Check Lecturer creation and account suspension with demonstration accounts.

## Security and audit
- CSRF is required on all admin updates, and privileged changes require the current administrator's password.
- Non-Super Admin users cannot create Admin accounts; neither web interface role can create another Super Admin.
- Self-suspension and Super Admin suspension are blocked; inactive accounts cannot reuse existing sessions.
- Lecturer reports require explicit student permission. Admin rights do not grant access to private chat, uploaded files or raw research answers.
- The initial one-time database promotion is an explicit owner action, outside the application's audit UI; record it in the deployment notes for the dissertation.
- Research participant records must remain unchanged. Do not claim the v2 questionnaire is institutionally approved without supporting evidence.
