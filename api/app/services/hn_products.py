from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product, ReceiptLine, Vendor
from app.money import parse_dkk_to_ore

USER_AGENT = "ReceiptsLedger/0.1 (+personal receipt ledger; product lookup)"
PRODUCT_URL = "https://www.harald-nyborg.dk/product/index?id={item_number}"


@dataclass
class LookupResult:
    item_number: str
    status: str
    title: str | None
    url: str | None
    image_url: str | None
    last_web_price_ore: int | None


def _parse_product_page(html: str, item_number: str) -> LookupResult:
    soup = BeautifulSoup(html, "html.parser")
    title = None
    heading = soup.find("h1")
    if heading:
        title = heading.get_text(" ", strip=True)

    price_ore = None
    page_text = soup.get_text(" ", strip=True)
    # "28,00 kr" appears near the add-to-cart block
    match = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*kr", page_text, re.IGNORECASE)
    if match:
        price_ore = parse_dkk_to_ore(match.group(1))

    image_url = None
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        image_url = og["content"]
    else:
        img = soup.find("img", src=re.compile(r"cdn\.bizzkit|haraldnyborg", re.I))
        if img and img.get("src"):
            image_url = img["src"]

    not_found = not title or "siden blev ikke fundet" in page_text.lower() or "page not found" in page_text.lower()
    url = PRODUCT_URL.format(item_number=item_number)
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        url = canonical["href"]

    return LookupResult(
        item_number=item_number,
        status="not_found" if not_found else "found",
        title=None if not_found else title,
        url=None if not_found else url,
        image_url=None if not_found else image_url,
        last_web_price_ore=None if not_found else price_ore,
    )


def fetch_harald_nyborg_product(item_number: str) -> LookupResult:
    url = PRODUCT_URL.format(item_number=item_number)
    with httpx.Client(timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        response = client.get(url)
        if response.status_code == 404:
            return LookupResult(item_number, "not_found", None, None, None, None)
        response.raise_for_status()
        return _parse_product_page(response.text, item_number)


def lookup_receipt_products(db: Session, receipt_id, vendor: Vendor) -> list[Product]:
    lines = list(
        db.scalars(select(ReceiptLine).where(ReceiptLine.receipt_id == receipt_id).order_by(ReceiptLine.position))
    )
    seen: set[str] = set()
    updated: list[Product] = []
    now = datetime.now(timezone.utc)

    for line in lines:
        item_number = (line.item_number or "").strip()
        if not item_number or item_number in seen:
            continue
        seen.add(item_number)

        product = db.scalar(
            select(Product).where(Product.vendor_id == vendor.id, Product.item_number == item_number)
        )
        if product is None:
            product = Product(vendor_id=vendor.id, item_number=item_number, status="pending")
            db.add(product)
            db.flush()

        try:
            result = fetch_harald_nyborg_product(item_number)
            product.status = result.status
            product.title = result.title
            product.url = result.url
            product.image_url = result.image_url
            product.last_web_price_ore = result.last_web_price_ore
            product.last_fetched_at = now
        except httpx.HTTPError:
            product.status = "error"
            product.last_fetched_at = now

        for same in lines:
            if same.item_number == item_number:
                same.product_id = product.id
        updated.append(product)

    db.commit()
    for product in updated:
        db.refresh(product)
    return updated
