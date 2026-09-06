# Household Ledger

A private website for one household’s **bank accounts** and **investments**. It is meant for you, your girlfriend, and her daughter: Nordea accounts, Nordnet depots, money in and out, receipts, and category totals.

The first run is empty except for the login in `.env`. You create people, platforms, and accounts yourself.

GitHub: [https://github.com/PsyCrow1976/recieptslegder](https://github.com/PsyCrow1976/recieptslegder)

## Purpose

Keep a single picture of household money:

- Who owns which account (including shared accounts)
- What came in and what went out
- Which vendor and category each amount belongs to
- How the balance moved through a month and a year

It is a website on Unraid, not a public API or a mobile app. Two Docker containers: Postgres and the site.

## How you set it up

1. **People** — household members who can own accounts.
2. **Platforms** — Nordea (bank), Nordnet (investment), or anything else.
3. **Accounts** — each account on a platform, with one owner or several if it is shared. For Nordea, put the register and account number on the account (for example `2112-9040298476`) so CSV import can match the file.
4. **Start amount** — on each account, the money that was there on a given date. Current balance is that amount plus entries **on or after** that date. Older entries stay in the list but do not change the balance.
5. **Vendors and categories** — optional, but useful before a large CSV import so names can be matched.
6. **Entries** — money in or out, by hand or from a bank CSV. An entry can have a vendor, categories, a PDF or photo, and line items (product, link, signed amount).

## Account views

Open an account for three views:

| View | What you see |
|------|----------------|
| **Month** | Dated statement: income in one column, expenses in the other, running balance after each line, start and end of month |
| **Year** | Jan–Dec totals per category for income and for expenses. No category → **Other**. Bottom row is the end-of-month balance. Click a month name to open that month |
| **List** | Long list with a from/to date range |

Home shows household total, this month in/out, accounts, and a short setup list until data exists.

## Nordea CSV import

**Entries → Import CSV** (or from an account).

1. Choose the account and the bank CSV (`Bogføringsdato;Beløb;…`).
2. Review every row: **new**, **duplicate** (already in the ledger), or **skipped** (for example *Reserveret*).
3. Vendors and categories are suggested from the name (exact match, close match, or create).
4. Import only the new rows. Importing the same file again marks those lines as duplicates.

Bank statement files can live locally under `input/<reg>-<account>/`. That folder is gitignored so statements are not pushed to GitHub.

## Stack

PostgreSQL 16 and one website container. Docker Compose. Amounts are øre (integers), shown as Danish DKK (`1.234,50 kr`). Time zone `Europe/Copenhagen`.

## Unraid

See **[deploy.md](deploy.md)** for a clean install.

Short version when the folder is empty:

```bash
mkdir -p /mnt/user/appdata/receiptslegder && cd /mnt/user/appdata/receiptslegder
git clone https://github.com/PsyCrow1976/recieptslegder.git .
cp .env.example .env && nano .env
mkdir -p postgres documents
cp docker-compose.override.example.yml docker-compose.override.yml
docker compose up -d --build
```

Open [http://192.168.1.130:8085](http://192.168.1.130:8085) and sign in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `.env`.

Later updates:

```bash
cd /mnt/user/appdata/receiptslegder
git pull
docker compose up -d --build
```

Database migrations run when the website container starts.

## Local development

```bash
cp .env.example .env
docker compose up -d --build
```

Open [http://localhost:8085](http://localhost:8085).

```bash
cd api
pip install -r requirements.txt
pytest
```
