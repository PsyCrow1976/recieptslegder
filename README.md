# Household Ledger

Family ledger for **bank accounts** and **investments**, with receipts and line items.

Create the people in the household, the platforms they use (Nordea, Nordnet, …), the accounts on those platforms (one owner or several), then record money going in or out. Each entry can have a vendor, categories, an attached PDF or photo, and one or more line items.

The first run is **empty**. Login is the admin user from `.env`. You add people, platforms, and accounts yourself.

GitHub: [https://github.com/PsyCrow1976/recieptslegder](https://github.com/PsyCrow1976/recieptslegder)

## What you can do

- **People** — household members (you, partner, child, …)
- **Platforms** — bank or investment house (Nordea, Nordnet, others)
- **Accounts** — named accounts on a platform, with one or more owners for shared accounts
- **Entries** — money in or money out, with vendor and optional categories
- **Line items** — split an entry into products; each item has vendor, product URL, and a signed amount
- **Documents** — PDF statements, receipt photos, or other files on an entry
- **Vendors & categories** — reusable, or typed inline on an entry

Amounts are stored in øre (integer). Display is Danish DKK (`1.234,50 kr`).

## Stack

PostgreSQL 16, FastAPI, React + Vite + Tailwind, nginx, Docker Compose.

## Unraid

See **[deploy.md](deploy.md)**.

This is a **breaking rewrite** of the old receipt-scanner app. Wipe the old Postgres data before starting (see deploy.md).

Short version:

```bash
mkdir -p /mnt/user/appdata/receiptslegder && cd /mnt/user/appdata/receiptslegder
git clone https://github.com/PsyCrow1976/recieptslegder.git .
cp .env.example .env && nano .env   # set passwords
cp docker-compose.override.example.yml docker-compose.override.yml
docker compose up -d --build
```

Open [http://192.168.1.130:8085](http://192.168.1.130:8085).

## Local development

```bash
cp .env.example .env
docker compose up -d --build
```

Open [http://localhost:8085](http://localhost:8085).

API docs: [http://localhost:8085/docs](http://localhost:8085/docs).

```bash
cd api
pip install -r requirements.txt
pytest
```

## First use

1. Sign in with `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
2. **People** — add everyone who owns an account.
3. **Platforms** — e.g. Nordea (bank), Nordnet (investment).
4. **Accounts** — create each account and assign owner(s).
5. **Entries** — money in or out. Attach a PDF or photo. Split into line items if you want.
