"""Interactive account provisioning; password values never enter command arguments."""

import argparse, getpass
from sqlalchemy import select
from .db import initialize, Session, User
from .security import hash_password


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["create-user", "reset-password"])
    parser.add_argument("email")
    parser.add_argument("--name")
    args = parser.parse_args()
    password = getpass.getpass("New password (12+ characters): ")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords differ")
    initialize()
    with Session.begin() as db:
        user = db.scalar(select(User).where(User.email == args.email.lower().strip()))
        if args.action == "create-user":
            if user:
                raise SystemExit("Account already exists")
            db.add(
                User(
                    email=args.email.lower().strip(),
                    name=args.name or args.email.split("@")[0],
                    password=hash_password(password),
                )
            )
        else:
            if not user:
                raise SystemExit("Account not found")
            user.password = hash_password(password)
            from sqlalchemy import delete
            from .db import LoginSession

            db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    print("Account updated. Add it to the required project in Project team.")


if __name__ == "__main__":
    main()
