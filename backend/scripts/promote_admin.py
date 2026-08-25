"""One-time bootstrap: grant admin access to an existing account.

There's no API endpoint that can create the first admin (an endpoint
callable by nobody-yet would be a privilege-escalation hole), so this is a
script you run yourself, once, directly against the database.

Usage (from backend/):
    python scripts/promote_admin.py you@example.com
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security.authentication import get_user_by_email  # noqa: E402
from security.db import SessionLocal, init_db  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/promote_admin.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    init_db()
    db = SessionLocal()
    try:
        user = get_user_by_email(db, email)
        if user is None:
            print(f"No account found for {email} — register that account first, then re-run this.")
            sys.exit(1)

        if user.is_admin:
            print(f"{email} is already an admin.")
            return

        user.is_admin = True
        db.commit()
        print(f"{email} is now an admin.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
