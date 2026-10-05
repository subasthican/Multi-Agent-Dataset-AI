# Gowsika — Individual Vulnerability Assessment Draft

**Specialization proposed:** Privacy and Data Leakage Assessment. Lecturer allocation remains unconfirmed.

**Authorship and submission status:** AI-assisted execution and drafting for the team. This document does not claim that Gowsika independently performed these tests. The individual brief requires independent student work: review and reproduce the cases, verify evidence and ratings, write your own reflection, and comply with course rules for AI assistance before submission. This is an evidence-backed draft, not a certified completed individual submission.

## Current Fix Status

The findings below preserve the original baseline. Application fixes and subsequent retesting are documented separately in [fix verification](../fix-verification/README.md). All 69 fixed-application checks passed; these include application input guards and controlled model outputs, not live Gemini jailbreak verification. Latest credential checks confirmed Gemini key acceptance and three authenticated Kaggle results. The earlier full attempt recorded 12 passing browser flows and a duplicate failure. That duplicate is now fixed: 23 new unit tests, 38 authored ranking/abstention cases and 3 HTTP checks pass; live Gemini evaluation remains daily-quota blocked. See [current application fixes](../fix-verification/remaining-fixes.md). See [credential feedback](../fix-verification/evidence/live-integrations/credential-feedback.json). Student details and personal reflections are deferred by the user.

## Executive Summary

DATA NEBULA AI was assessed at commit `244ee2712fafc98c63e85346552a809acbdd89df` on 2026-10-05T11:26:38.325053+05:30. This scope recorded 15 cases: **10 PASS, 5 FAIL, 0 BLOCKED**. Passing means the selected criterion held in this observation; it does not establish general safety. Failed means the criterion did not hold; blocked means the required execution could not complete. 4 supported finding categories are discussed below. No application source fixes were made during this assessment.

Major findings: Reset response distinguishes registered emails; Synthetic identifiers are retained verbatim and included in prompt construction; Unauthenticated password reset permits controlled-account takeover; Previously issued JWT survives password change.

## Scope of Testing

Authentication, authorization, JWT lifetime, password-reset capabilities, application-visible history handling, permitted admin access, synthetic PII persistence and prompt construction. No live PII transmitted; PR-04 substitutes an empty retrieval result only to isolate the real history/profile access logic.

The production/local working database was not used for testing. Accounts and records were synthetic in a temporary SQLite database. HTTP route tests use FastAPI TestClient in-process, not a deployed browser session or external network ingress. TLS, reverse proxies, provider retention, cloud infrastructure, payments and legal/privacy compliance are not certified by this assessment. Screenshots were not captured; JSON request/response and component logs provide evidence.

All members must understand the full architecture: Next.js → FastAPI → NLP understanding → local/live retrieval → evaluation → ranked dataset metadata; signed-in history powers personalization. Internal agents are Python modules, not separate network services.

## Evaluation Methodology

1. Preserve baseline code and record its Git commit and database checksum.
2. Create synthetic test accounts and isolated storage; seed the real catalog/plans.
3. Execute defined scenarios with explicit expected behavior. Use real application routes or identified component calls; disclose test substitutions and deterministic configurations.
4. Record actual statuses, bodies, inputs, model traces or component outputs per test. Redact credentials and capabilities from saved evidence.
5. Compare observations with the stated criterion and map supported failures to findings.
6. Assess risk in the tested context; recommend mitigations without claiming they were implemented or validated.

Environment: Python `3.13.7`, `macOS-26.5.1-arm64-arm-64bit-Mach-O`. Exact installed package versions are in [requirements-lock.txt](evidence/requirements-lock.txt); transport/configuration and database checksums are in [manifest.json](evidence/manifest.json). Backend requirements are unpinned, so this installed environment may differ from previous developer runs. Gemini configured model: `gemini-3.5-flash`; credential configured: `True`. No credential values are published.

Risk rating: impact and likelihood each use Low=1, Medium=2, High=3. Product 1=Low, 2–3=Medium, 4–6=High, 9=Critical. Informational is reserved for non-adverse observations. This is a disclosed project matrix, not a formal CVSS score. Ratings are provisional and should be reviewed by the student using deployment context.

## Test Cases Performed

| ID | Objective | Outcome | Evidence |
|---|---|---|---|
| PR-01 | Unauthenticated profile access | PASS | [JSON log](evidence/PR-01.json) |
| PR-02 | Tampered JWT | PASS | [JSON log](evidence/PR-02.json) |
| PR-03 | Expired JWT | PASS | [JSON log](evidence/PR-03.json) |
| PR-04 | Cross-user history access | PASS | [JSON log](evidence/PR-04.json) |
| PR-05 | Normal-user admin access | PASS | [JSON log](evidence/PR-05.json) |
| PR-06 | Password-hash exposure | PASS | [JSON log](evidence/PR-06.json) |
| PR-07 | Account enumeration | FAIL | [JSON log](evidence/PR-07.json) |
| PR-08 | Reset-token disclosure | FAIL | [JSON log](evidence/PR-08.json) |
| PR-09 | Reset without email ownership | FAIL | [JSON log](evidence/PR-09.json) |
| PR-10 | Reset-token reuse | PASS | [JSON log](evidence/PR-10.json) |
| PR-11 | Expired reset token | PASS | [JSON log](evidence/PR-11.json) |
| PR-12 | JWT after password change | FAIL | [JSON log](evidence/PR-12.json) |
| PR-13 | Suspended-account token | PASS | [JSON log](evidence/PR-13.json) |
| PR-14 | Synthetic PII handling | FAIL | [JSON log](evidence/PR-14.json) |
| PR-15 | History deletion | PASS | [JSON log](evidence/PR-15.json) |

### PR-01 — Unauthenticated profile access

- **Objective:** Unauthenticated profile access.
- **Input / scenario:** GET /auth/me, no token
- **Expected behavior:** 401 and no profile data.
- **Actual behavior:**

```json
{
  "status": 401,
  "response": {
    "detail": "Not authenticated"
  }
}
```

- **Evidence:** [PR-01.json](evidence/PR-01.json), including request/model/component trace where available.
- **Observations:** Access denied as expected.
- **Conclusion / outcome:** PASS. Access denied as expected.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-02 — Tampered JWT

- **Objective:** Tampered JWT.
- **Input / scenario:** GET /auth/me with modified signature
- **Expected behavior:** 401 and no profile data.
- **Actual behavior:**

```json
{
  "status": 401,
  "response": {
    "detail": "Not authenticated"
  }
}
```

- **Evidence:** [PR-02.json](evidence/PR-02.json), including request/model/component trace where available.
- **Observations:** Access denied as expected.
- **Conclusion / outcome:** PASS. Access denied as expected.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-03 — Expired JWT

- **Objective:** Expired JWT.
- **Input / scenario:** GET /auth/me with expired controlled token
- **Expected behavior:** 401 and no profile data.
- **Actual behavior:**

```json
{
  "status": 401,
  "response": {
    "detail": "Not authenticated"
  }
}
```

- **Evidence:** [PR-03.json](evidence/PR-03.json), including request/model/component trace where available.
- **Observations:** Access denied as expected.
- **Conclusion / outcome:** PASS. Access denied as expected.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-04 — Cross-user history access

- **Objective:** Cross-user history access.
- **Input / scenario:** A requests B’s admin detail and own personalized profile
- **Expected behavior:** 403 for B; A-only history profile.
- **Actual behavior:**

```json
{
  "other_user_status": 403,
  "own_profile": {
    "based_on_domain": "healthcare",
    "based_on_task": "classification",
    "search_count": 1,
    "recommendations": []
  },
  "fixture": "Only recommendation retrieval replaced with empty result; auth, history lookup and profile building are real."
}
```

- **Evidence:** [PR-04.json](evidence/PR-04.json), including request/model/component trace where available.
- **Observations:** User A could not access B; A’s profile used A’s history only.
- **Conclusion / outcome:** PASS. User A could not access B; A’s profile used A’s history only.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-05 — Normal-user admin access

- **Objective:** Normal-user admin access.
- **Input / scenario:** A requests admin users and stats
- **Expected behavior:** 403 for both routes.
- **Actual behavior:**

```json
[
  403,
  403
]
```

- **Evidence:** [PR-05.json](evidence/PR-05.json), including request/model/component trace where available.
- **Observations:** Normal user denied both admin routes.
- **Conclusion / outcome:** PASS. Normal user denied both admin routes.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-06 — Password-hash exposure

- **Objective:** Password-hash exposure.
- **Input / scenario:** Inspect profile, admin, login and registration responses
- **Expected behavior:** No plaintext password or hash in responses.
- **Actual behavior:**

```json
{
  "statuses": [
    200,
    200,
    200,
    201
  ],
  "returned_keys": [
    [
      "id",
      "name",
      "email",
      "plan",
      "is_admin",
      "is_active",
      "created_at"
    ],
    [
      "id",
      "name",
      "email",
      "plan",
      "is_admin",
      "is_active",
      "created_at",
      "search_count"
    ],
    [
      "access_token",
      "token_type"
    ],
    [
      "access_token",
      "token_type"
    ]
  ]
}
```

- **Evidence:** [PR-06.json](evidence/PR-06.json), including request/model/component trace where available.
- **Observations:** Inspected API response bodies exclude plaintext passwords and hashes.
- **Conclusion / outcome:** PASS. Inspected API response bodies exclude plaintext passwords and hashes.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-07 — Account enumeration

- **Objective:** Account enumeration.
- **Input / scenario:** Compare reset responses for registered and unregistered synthetic emails
- **Expected behavior:** No account-existence disclosure.
- **Actual behavior:**

```json
{
  "existing": {
    "message": "If that email is registered, a reset link has been sent.",
    "dev_reset_token": "[REDACTED]"
  },
  "nonexistent": {
    "message": "If that email is registered, a reset link has been sent.",
    "dev_reset_token": null
  }
}
```

- **Evidence:** [PR-07.json](evidence/PR-07.json), including request/model/component trace where available.
- **Observations:** Non-null reset token distinguishes registered account from nonexistent account.
- **Conclusion / outcome:** FAIL. Non-null reset token distinguishes registered account from nonexistent account.
- **Finding references:** PR-ENUM

### PR-08 — Reset-token disclosure

- **Objective:** Reset-token disclosure.
- **Input / scenario:** Unauthenticated forgot-password for controlled B
- **Expected behavior:** No token returned to requester.
- **Actual behavior:**

```json
{
  "status": 200,
  "token_present": true
}
```

- **Evidence:** [PR-08.json](evidence/PR-08.json), including request/model/component trace where available.
- **Observations:** Public API exposes a usable reset capability.
- **Conclusion / outcome:** FAIL. Public API exposes a usable reset capability.
- **Finding references:** PR-RESET

### PR-09 — Reset without email ownership

- **Objective:** Reset without email ownership.
- **Input / scenario:** Reset B knowing only its test email, then verify new login
- **Expected behavior:** Cannot take over account without ownership verification.
- **Actual behavior:**

```json
{
  "reset_status": 204,
  "new_password_login_status": 200
}
```

- **Evidence:** [PR-09.json](evidence/PR-09.json), including request/model/component trace where available.
- **Observations:** Unauthenticated caller reset B using only its email and successfully logged in with the new password.
- **Conclusion / outcome:** FAIL. Unauthenticated caller reset B using only its email and successfully logged in with the new password.
- **Finding references:** PR-RESET

### PR-10 — Reset-token reuse

- **Objective:** Reset-token reuse.
- **Input / scenario:** Consume controlled reset token twice
- **Expected behavior:** Second consumption rejected.
- **Actual behavior:**

```json
{
  "first": 204,
  "second": 400,
  "first_password_login": 200
}
```

- **Evidence:** [PR-10.json](evidence/PR-10.json), including request/model/component trace where available.
- **Observations:** Consumed token rejected on reuse; original reset password retained.
- **Conclusion / outcome:** PASS. Consumed token rejected on reuse; original reset password retained.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-11 — Expired reset token

- **Objective:** Expired reset token.
- **Input / scenario:** Move controlled token expiry into past, attempt reset
- **Expected behavior:** Rejected, password unchanged.
- **Actual behavior:**

```json
{
  "expired_reset_status": 400,
  "unchanged_password_login": 200,
  "fixture": "Expiry moved into past in isolated DB."
}
```

- **Evidence:** [PR-11.json](evidence/PR-11.json), including request/model/component trace where available.
- **Observations:** Expired token rejected; password unchanged.
- **Conclusion / outcome:** PASS. Expired token rejected; password unchanged.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-12 — JWT after password change

- **Objective:** JWT after password change.
- **Input / scenario:** Change A’s password then reuse pre-change token
- **Expected behavior:** Old compromised token should be revoked.
- **Actual behavior:**

```json
{
  "password_change": 204,
  "old_token_profile": 200
}
```

- **Evidence:** [PR-12.json](evidence/PR-12.json), including request/model/component trace where available.
- **Observations:** Old JWT remains usable after password change; application has no session-version check.
- **Conclusion / outcome:** FAIL. Old JWT remains usable after password change; application has no session-version check.
- **Finding references:** PR-SESSION

### PR-13 — Suspended-account token

- **Objective:** Suspended-account token.
- **Input / scenario:** Admin suspends B, B retries /auth/me
- **Expected behavior:** Existing token rejected immediately.
- **Actual behavior:**

```json
{
  "suspend": 200,
  "existing_token": 401
}
```

- **Evidence:** [PR-13.json](evidence/PR-13.json), including request/model/component trace where available.
- **Observations:** Suspended account’s old token immediately denied on protected route.
- **Conclusion / outcome:** PASS. Suspended account’s old token immediately denied on protected route.
- **Finding references:** No supported vulnerability assigned by this case.

### PR-14 — Synthetic PII handling

- **Objective:** Synthetic PII handling.
- **Input / scenario:** Store a fake query through record_search; inspect admin view and prompt construction
- **Expected behavior:** Minimize sensitive data and document access/transmission.
- **Actual behavior:**

```json
{
  "raw_query_persisted": true,
  "admin_can_view": true,
  "PII_in_prompt": true,
  "network_send_performed": false
}
```

- **Evidence:** [PR-14.json](evidence/PR-14.json), including request/model/component trace where available.
- **Observations:** Synthetic PII stored verbatim, exposed to admins, and included in provider-bound prompt construction; actual provider transmission not tested.
- **Conclusion / outcome:** FAIL. Synthetic PII stored verbatim, exposed to admins, and included in provider-bound prompt construction; actual provider transmission not tested.
- **Finding references:** PR-PII

### PR-15 — History deletion

- **Objective:** History deletion.
- **Input / scenario:** Clear A’s history and inspect DB/admin/recommendations
- **Expected behavior:** A removed; B preserved.
- **Actual behavior:**

```json
{
  "delete_status": 204,
  "A_rows_after": 0,
  "B_rows_before": 1,
  "B_rows_after": 1,
  "admin_history": [],
  "own_profile": {
    "based_on_domain": null,
    "based_on_task": null,
    "search_count": 0,
    "recommendations": []
  }
}
```

- **Evidence:** [PR-15.json](evidence/PR-15.json), including request/model/component trace where available.
- **Observations:** A’s history and profile cleared; B unchanged. This proves application-visible logical deletion, not forensic erasure of disk pages/backups.
- **Conclusion / outcome:** PASS. A’s history and profile cleared; B unchanged. This proves application-visible logical deletion, not forensic erasure of disk pages/backups.
- **Finding references:** No supported vulnerability assigned by this case.

## Vulnerabilities Identified

### PR-ENUM — Reset response distinguishes registered emails

- **Description and technical explanation:** The registered response includes a non-null token; nonexistent emails return null despite identical message text. This reveals membership and supports targeted attacks. It is a supporting aspect of PR-RESET, not a separate takeover mechanism.
- **Affected implementation:** `backend/security/router.py: forgot_password`.
- **Evidence:** [PR-07](evidence/PR-07.json).
- **Impact:** Low. See the scenario-specific effect described above.
- **Likelihood:** High. Assessed in the context and prerequisites described above.
- **Severity / risk level:** Medium, using the disclosed impact × likelihood matrix.
- **Mitigation:** Return the same public response shape regardless of account existence, never include a usable reset token, and limit automated probing.

### PR-PII — Synthetic identifiers are retained verbatim and included in prompt construction

- **Description and technical explanation:** The real persistence function stores the fake email/phone query without redaction and the permitted admin view returns it. Prompt construction also retains it. Access is admin-restricted; unauthorized database access and actual provider transmission were not demonstrated. This is a data-minimization/privacy-design finding, not a legal compliance conclusion.
- **Affected implementation:** `backend/agents/recommendation_agent/agent.py: record_search; backend/security/admin_router.py: get_user_detail; backend/llm/prompts.py`.
- **Evidence:** [PR-14](evidence/PR-14.json).
- **Impact:** Medium. See the scenario-specific effect described above.
- **Likelihood:** Low. Assessed in the context and prerequisites described above.
- **Severity / risk level:** Medium, using the disclosed impact × likelihood matrix.
- **Mitigation:** Minimize or redact identifiers before persistence and external model submission; offer a personalization opt-out, explicit purpose/access disclosure, retention/deletion policy, and least-privilege administrative access. Evaluate encryption against a defined storage threat model.

### PR-RESET — Unauthenticated password reset permits controlled-account takeover

- **Description and technical explanation:** The unauthenticated forgot-password route returns a reset token. A requester who knows a registered email can use it to change that account’s password and log in. Critical reflects account compromise without a prior authenticated foothold when this demo behavior is exposed; no public deployment was tested.
- **Affected implementation:** `backend/security/router.py: forgot_password and reset_password; backend/security/password_reset.py`.
- **Evidence:** [PR-08](evidence/PR-08.json), [PR-09](evidence/PR-09.json).
- **Impact:** High. See the scenario-specific effect described above.
- **Likelihood:** High. Assessed in the context and prerequisites described above.
- **Severity / risk level:** Critical, using the disclosed impact × likelihood matrix.
- **Mitigation:** Deliver reset capabilities exclusively to a verified email channel. Disable response tokens outside explicitly isolated development mode. Store a token digest, limit requests, and invalidate outstanding reset tokens/sessions after successful recovery.

### PR-SESSION — Previously issued JWT survives password change

- **Description and technical explanation:** A controlled password change succeeds but the pre-change JWT still accesses the account. Exploitation requires a previously stolen token; it does not enable stealing a token on its own. Risk lasts until expiration.
- **Affected implementation:** `backend/security/router.py: change_password; backend/security/jwt_manager.py; backend/security/authentication.py`.
- **Evidence:** [PR-12](evidence/PR-12.json).
- **Impact:** High. See the scenario-specific effect described above.
- **Likelihood:** Medium. Assessed in the context and prerequisites described above.
- **Severity / risk level:** High, using the disclosed impact × likelihood matrix.
- **Mitigation:** Add a server-side token/session version or revoke sessions issued before password changes and recovery. Test the old token as well as a fresh login.

## Risk Assessment

| Finding | Impact | Likelihood | Risk level |
|---|---|---|---|
| PR-ENUM: Reset response distinguishes registered emails | Low | High | Medium |
| PR-PII: Synthetic identifiers are retained verbatim and included in prompt construction | Medium | Low | Medium |
| PR-RESET: Unauthenticated password reset permits controlled-account takeover | High | High | Critical |
| PR-SESSION: Previously issued JWT survives password change | High | Medium | High |

## Mitigation Strategies

- **PR-ENUM:** Return the same public response shape regardless of account existence, never include a usable reset token, and limit automated probing.
- **PR-PII:** Minimize or redact identifiers before persistence and external model submission; offer a personalization opt-out, explicit purpose/access disclosure, retention/deletion policy, and least-privilege administrative access. Evaluate encryption against a defined storage threat model.
- **PR-RESET:** Deliver reset capabilities exclusively to a verified email channel. Disable response tokens outside explicitly isolated development mode. Store a token digest, limit requests, and invalidate outstanding reset tokens/sessions after successful recovery.
- **PR-SESSION:** Add a server-side token/session version or revoke sessions issued before password changes and recovery. Test the old token as well as a fresh login.

Retest each adopted change at a new commit using the same baseline input and record new evidence separately. Do not overwrite baseline observations with assumed fixed outcomes.

## Reflection

The privacy assessment exposed a distinction between strong password storage and safe account recovery. PR-06 found no passwords or hashes in the inspected responses, and PR-01–05 showed the tested authentication/authorization checks worked. Nevertheless, PR-08–09 demonstrated that a public reset capability bypassed email ownership and enabled a controlled-account takeover. PR-12 showed why changing a password does not automatically revoke stateless JWTs. A methodological challenge was testing failures without changing real accounts: synthetic identities and temporary storage allowed reset, suspension and deletion scenarios to be executed safely. PR-14 separated persistence and prompt construction from actual provider transmission; its result supports a data-minimization concern, not an allegation of observed external leakage or legal noncompliance. Future work should implement verified recovery, session revocation and purpose-limited retention, then separately retest old/new tokens, user isolation and deletion. The student should adapt this analysis using their own reproduction experience before submission.

## Individual Viva Preparation

These are evidence-grounded study answers. Independently verify the cases before presenting them as your own work. Viva attendance and performance cannot be completed by this document.

### What was your scope and method?

I need to independently reproduce the recorded privacy assessment. The draft uses synthetic users and an isolated SQLite database, tests actual FastAPI routes with TestClient, and checks storage through real application functions. It does not test a publicly deployed server, TLS or provider retention.

### What is the strongest supported finding?

PR-09 obtained a reset token using only a controlled account's email, reset its password with status 204, then logged in using the replacement password with status 200. That demonstrates account takeover in the tested configuration.

### Why is account takeover rated Critical?

Its impact is High and likelihood High when this public demo endpoint is exposed: no existing login or email-ownership proof is needed. The defined matrix maps 3 × 3 to Critical. No actual public deployment was assessed.

### Why do password hashes not solve this?

bcrypt protects password verification/storage. The reset endpoint can replace the stored hash without knowing the old password because it trusts a publicly returned token. These are different trust boundaries.

### Which controls resisted the tested attacks?

Missing, tampered and expired tokens were rejected; normal users were denied tested admin access; a suspended account's existing token was denied on the protected profile route. A passing case proves only that scenario.

### Why did an old JWT survive a password change?

JWT signature and expiry checks are independent of the stored password. The current authorization code does not compare a session version or revocation timestamp against password changes.

### Did you prove another user's history was leaked?

No. PR-04 denied normal-user access to another user's admin detail and confirmed own-user profile isolation. PR-14 demonstrated permitted admin access to unredacted synthetic identifiers, not unauthorized cross-user leakage.

### Did you prove Gemini received PII?

No. The synthetic PII case tested actual persistence and prompt construction without sending the identifiers externally. It proves inclusion in the provider-bound prompt, not transmission or provider retention.

### What does the deletion test prove?

PR-15 removed A's application-visible history and personalization while preserving B's rows. It does not prove forensic erasure from SQLite pages, backups or upstream logs.

### What would you fix and retest first?

Stop returning reset capabilities publicly; deliver them only through a verified channel, revoke sessions after recovery/password changes, and retest takeover and old-token access. Validate data minimization and access policies separately.

## References

- [Individual Assignment Brief](../Individual%20Assignment%20Brief.pdf): specialization, minimum tests, evidence, report sections and viva criteria.
- [Group Assignment Brief](../Group%20Assignment%20Brief.pdf): system scope and group deliverables.
- Local application code and recorded case logs referenced above. No external standard compliance is claimed.

## Remaining Submission Work

- [ ] Confirm specialization and student ID with lecturer/member.
- [ ] Independently reproduce and validate cases; complete blocked live cases using a valid local key.
- [ ] Review conclusions/ratings and adapt the evidence-based reflection using your own experience.
- [ ] Apply any required institutional report template and finalize authorship under course AI-assistance rules.
- [ ] Attend and defend the individual viva.
