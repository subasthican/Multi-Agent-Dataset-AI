# Security implementation and assessment status

## Implemented controls

Passwords are bcrypt-hashed with the 72-byte input boundary checked. Signed JWTs are bound to the current password hash and authorization rechecks user activity and admin status. Password change/recovery invalidates previously issued sessions. Password recovery returns a generic public message, stores token digests, enforces expiry and atomic single-use claiming, and invalidates remaining reset tokens after recovery. SMTP delivery is implemented but local configuration/testing is deferred at the user's request.

Input guards reject explicit overrides and selected discriminatory requests. Model outputs are validated using strict allowlisted fields and bounded flat keyword lists, with safe fallback. Email/phone patterns are minimized before prompt construction and history persistence. These are finite heuristic protections, not universal detection or comprehensive personal-data anonymization.

AI request usage is held in atomic daily counters independent of deletable search history. Standalone AI endpoints share the quota. Anonymous counter subjects use an HMAC of the TCP peer address; reverse-proxy deployment needs an explicit trusted client-address policy.

Admin mutation auditing records actor and target IDs, action, timestamp and changed field names in the same transaction as successful changes. Passwords and sensitive field values are excluded. Audit viewing is admin-only; no mutation endpoint is exposed for the logs. User/catalog/plan deletions require the current password. Failed confirmations are recorded and five failures within 15 minutes throttle further attempts. The frontend provides a masked password dialog and activity viewer.

## Verification and limits

See [fix verification](fix-verification/README.md) for **69 passing cases**, source hashes and isolated JSON evidence. The database migration passed twice on a copy; real working records were not modified by tests. Frontend lint/type/build checks and backend compilation passed. Original audit failures remain archived separately.

Google rejects the configured key as reported leaked, so live model jailbreak evaluation remains blocked. Student IDs, confirmed specializations, personal reflections, independent reproduction and viva cannot be supplied as completed work by this implementation. Actual SMTP and deployed browser/network operation remain unverified. Stored search text now uses authenticated Fernet encryption through the ORM. Existing local history was migrated after an encrypted backup was created; all 26 history rows remained readable. SQLite administrators can alter audit records; external immutable logging, storage access controls, retention policy and production deployment review remain separate decisions. No claim of 100% security or completed individual assessment is made.
