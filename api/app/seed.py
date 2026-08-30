from sqlalchemy import select

from app.auth import hash_password
from app.config import settings
from app.database import SessionLocal
from app.models import User, Vendor

HARALD_NYBORG = {
    "slug": "harald-nyborg",
    "name": "Harald Nyborg",
    "cvr": "37783315",
    "base_url": "https://www.harald-nyborg.dk",
    "product_url_template": "https://www.harald-nyborg.dk/product/index?id={item_number}",
}


def seed() -> None:
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.username == settings.admin_username))
        if not admin:
            db.add(
                User(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                )
            )

        vendor = db.scalar(select(Vendor).where(Vendor.slug == HARALD_NYBORG["slug"]))
        if not vendor:
            db.add(Vendor(**HARALD_NYBORG))
        else:
            vendor.name = HARALD_NYBORG["name"]
            vendor.cvr = HARALD_NYBORG["cvr"]
            vendor.base_url = HARALD_NYBORG["base_url"]
            vendor.product_url_template = HARALD_NYBORG["product_url_template"]

        db.commit()


if __name__ == "__main__":
    seed()
    print("Seed complete.")
