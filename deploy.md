# Deploy Household Ledger on Unraid (Docker Compose)

**Your server:** `192.168.1.130`  
**App URL after install:** `http://192.168.1.130:8085`

Port **8085** is used so this stack does not collide with FitLineVentory on **8080**.

This rewrite **replaces** the old receipt-scanner database. You must wipe Postgres data from the previous version before starting.

---

## What gets installed

| Container | Role |
|-----------|------|
| `db` | PostgreSQL 16 — people, platforms, accounts, entries |
| `api` | FastAPI — ledger and file uploads |
| `web` | nginx — web UI + API proxy on port `8085` |

Uploaded PDFs and receipt photos are stored on a Docker volume (or Unraid appdata if you use the override file).

---

## Prerequisites

1. Docker enabled on Unraid.
2. Docker Compose (Compose Manager Plus from **Apps** is the usual option).
3. Git.
4. Port **8085** free, or change `HTTP_PORT` in `.env`.

```bash
ssh root@192.168.1.130
docker compose version
```

---

## Breaking upgrade from the receipt scanner

If you already ran the old app:

```bash
cd /mnt/user/appdata/receiptslegder
docker compose down
# Keep a copy if you still want old receipt data, then:
rm -rf /mnt/user/appdata/receiptslegder/postgres
rm -rf /mnt/user/appdata/receiptslegder/receipts
git fetch origin
git reset --hard origin/main
```

If you used the named Docker volume instead of appdata:

```bash
docker compose down -v
```

`-v` deletes the database. That is required for this schema.

---

## Fresh install

### Step 1 — Folder

```bash
mkdir -p /mnt/user/appdata/receiptslegder
cd /mnt/user/appdata/receiptslegder
```

### Step 2 — Clone

```bash
git clone https://github.com/PsyCrow1976/recieptslegder.git .
```

If the folder is not empty, clone into a subfolder or `git pull` / `git reset --hard origin/main`.

### Step 3 — Environment

```bash
cp .env.example .env
nano .env
```

Change at least:

| Variable | Notes |
|----------|--------|
| `POSTGRES_PASSWORD` | Must match the password in `DATABASE_URL` |
| `JWT_SECRET` | Long random string |
| `ADMIN_PASSWORD` | Web login password |

```env
HTTP_PORT=8085
POSTGRES_USER=receiptslegder
POSTGRES_PASSWORD=your-strong-db-password
POSTGRES_DB=receiptslegder
DATABASE_URL=postgresql+psycopg://receiptslegder:your-strong-db-password@db:5432/receiptslegder
JWT_SECRET=your-long-random-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
CORS_ORIGINS=http://localhost:8085,http://192.168.1.130:8085
TZ=Europe/Copenhagen
```

### Step 4 — Store data on appdata (recommended)

```bash
mkdir -p /mnt/user/appdata/receiptslegder/postgres
mkdir -p /mnt/user/appdata/receiptslegder/documents
cp docker-compose.override.example.yml docker-compose.override.yml
```

### Step 5 — Start

```bash
cd /mnt/user/appdata/receiptslegder
docker compose up -d --build
docker compose ps
```

Or Unraid **Compose Manager**: stack path `/mnt/user/appdata/receiptslegder/docker-compose.yml`, env path `.env`.

### Step 6 — Verify

```bash
curl http://localhost:8085/health
```

Expected: `{"status":"ok"}`

Open `http://192.168.1.130:8085` and sign in.

API docs: `http://192.168.1.130:8085/docs`

---

## First use

The database has **no people, platforms, accounts, or entries**.

1. **People** — you, your girlfriend, her daughter.
2. **Platforms** — Nordea (bank), Nordnet (investment), anything else.
3. **Accounts** — each account on a platform; pick one owner or several for a shared account.
4. **Entries** — money in or out. Attach PDF / photo. Add line items with vendor, product link, and amount.

---

## Updating

```bash
cd /mnt/user/appdata/receiptslegder
git pull
docker compose up -d --build
```

Migrations run when the API container starts.

---

## Backup

```bash
docker compose exec db pg_dump -U receiptslegder receiptslegder > backup-$(date +%F).sql
```

Also back up `/mnt/user/appdata/receiptslegder/postgres` and `documents` if you used Step 4.

---

## Purge the database (100%)

Stops the stack, deletes Postgres and uploaded files, then recreates an empty database and the admin login from `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).

```bash
cd /mnt/user/appdata/receiptslegder
git pull
docker compose down
rm -rf postgres documents
mkdir -p postgres documents
docker volume rm receiptslegder_postgres_data receiptslegder_documents 2>/dev/null || true
docker compose up -d --build
```

Wait until `docker compose ps` shows `db` healthy and `api` up, then sign in with the values in `.env`.

`DATABASE_URL` must use the same password as `POSTGRES_PASSWORD`.

---

## Troubleshooting

### 502 Bad Gateway

Wait for migrations, then `docker compose logs api --tail 50`.

### Login fails

Sign in with `ADMIN_USERNAME` and `ADMIN_PASSWORD` from `.env`. The API now applies those values on every start. If login still fails, run **Purge the database** above.

### Alembic / schema errors after git pull

This schema is new. Wipe Postgres as in **Purge the database** above.
