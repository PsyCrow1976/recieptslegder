from sqlalchemy import select

from app.auth import hash_password
from app.config import settings
from app.database import SessionLocal
from app.models import LoginUser


def seed() -> None:
    """Keep the household login in sync with ADMIN_USERNAME / ADMIN_PASSWORD in .env."""
    with SessionLocal() as db:
        admin = db.scalar(select(LoginUser).where(LoginUser.username == settings.admin_username))
        if admin:
            admin.password_hash = hash_password(settings.admin_password)
        else:
            db.add(
                LoginUser(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                )
            )
        db.commit()


if __name__ == "__main__":
    seed()
    print("Seed complete.")
