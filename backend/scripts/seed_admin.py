"""Idempotent bootstrap: create (or reset) a known-credentials admin account.

`promote_admin.py` needs an account to already exist and doesn't give you
its password back — useful once you already have an account, but not a fast
path to "just give me admin login credentials." This does that: creates the
account if it's missing, or resets its password if it already exists, and
grants admin either way. Safe to run repeatedly.

Usage (from backend/):
    python scripts/seed_admin.py
    python scripts/seed_admin.py --email you@example.com --password "..." --name "Your Name"

Local dev/demo convenience only — never leave the default credentials in
place on a real deployment.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security.authentication import get_user_by_email, hash_password, register_user  # noqa: E402
from security.db import SessionLocal, init_db  # noqa: E402

DEFAULT_EMAIL = "admin@datanebula.ai"
DEFAULT_PASSWORD = "AdminSeed123!"
DEFAULT_NAME = "Admin"
# Cosmetic only — is_admin bypasses the plan's search limit entirely
# regardless of which plan is set here (see security/usage_limits.py).
DEFAULT_PLAN = "enterprise"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset a known admin account.")
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--name", default=DEFAULT_NAME)
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        user = get_user_by_email(db, args.email)
        if user is None:
            user = register_user(db, args.name, args.email, args.password)
            print(f"Created account {args.email}.")
        else:
            user.hashed_password = hash_password(args.password)
            print(f"Account {args.email} already existed — password reset to the given value.")

        if user.is_admin:
            print(f"{args.email} was already an admin.")
        else:
            user.is_admin = True
            print(f"{args.email} promoted to admin.")

        user.plan = DEFAULT_PLAN
        db.commit()

        print(f"\nLogin with:\n  email:    {args.email}\n  password: {args.password}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
