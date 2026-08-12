import argparse

from . import models
from .database import SessionLocal
from .main import hash_password


def main():
    parser = argparse.ArgumentParser(description="Reset a user password locally.")
    parser.add_argument("--username", required=True, help="Username to reset")
    parser.add_argument("--password", required=True, help="New password (min 8 chars)")
    args = parser.parse_args()

    if len(args.password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == args.username.strip()).first()
        if user is None:
            raise SystemExit("User not found.")

        user.password_hash = hash_password(args.password)
        db.commit()
        print(f"Password updated for user '{user.username}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
