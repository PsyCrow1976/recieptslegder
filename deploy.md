# Deploy Household Ledger on Unraid (clean install)

Empty folder, current repo, two containers. No leftover database, no old `api` container.

**Server:** `192.168.1.130`  
**URL:** `http://192.168.1.130:8085`  
**Port:** `8085` (avoids FitLineVentory on `8080`)

| Container | Role |
|-----------|------|
| `db` | PostgreSQL 16 |
| `web` | The website on port `8085` |

---

## Prerequisites

SSH in:

```bash
ssh root@192.168.1.130
```

Need Docker, `docker compose`, and git. Port **8085** must be free.

```bash
docker compose version
git --version
```

If Compose is missing, Unraid **Apps** → **Compose Manager Plus**.

If an old stack is still running after you deleted the folder:

```bash
docker ps -a | grep receiptslegder
docker rm -f receiptslegder-db-1 receiptslegder-web-1 receiptslegder-api-1 2>/dev/null
docker volume ls | grep receiptslegder
docker volume rm receiptslegder_postgres_data receiptslegder_documents 2>/dev/null
```

---

## Clean install

### 1. Folder and clone

```bash
mkdir -p /mnt/user/appdata/receiptslegder
cd /mnt/user/appdata/receiptslegder
git clone https://github.com/PsyCrow1976/recieptslegder.git .
```

The trailing `.` clones **into this folder**. Confirm you see `docker-compose.yml`, `.env.example`, and `deploy.md`.

### 2. Passwords (`.env`)

```bash
cp .env.example .env
nano .env
```

Set all three of these, and use the **same** database password in both `POSTGRES_PASSWORD` and `DATABASE_URL`:

```env
HTTP_PORT=8085
POSTGRES_USER=receiptslegder
POSTGRES_PASSWORD=your-strong-db-password
POSTGRES_DB=receiptslegder
DATABASE_URL=postgresql+psycopg://receiptslegder:your-strong-db-password@db:5432/receiptslegder
JWT_SECRET=your-long-random-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
TZ=Europe/Copenhagen
```

| Variable | Meaning |
|----------|---------|
| `POSTGRES_PASSWORD` | Database password (must match `DATABASE_URL`) |
| `JWT_SECRET` | Random string for login cookies/tokens |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Website login. Applied every time `web` starts |

Save: `Ctrl+O`, Enter, `Ctrl+X`.

### 3. Store data on appdata

```bash
mkdir -p /mnt/user/appdata/receiptslegder/postgres
mkdir -p /mnt/user/appdata/receiptslegder/documents
cp docker-compose.override.example.yml docker-compose.override.yml
```

That keeps Postgres and uploaded PDFs/photos on the Unraid share so backups are obvious.

### 4. Build and start

```bash
cd /mnt/user/appdata/receiptslegder
docker compose up -d --build
docker compose ps
```

First build can take a few minutes. You want `db` **healthy** and `web` **Up**.

Compose Manager: stack path `/mnt/user/appdata/receiptslegder/docker-compose.yml`, env path `/mnt/user/appdata/receiptslegder/.env`.

### 5. Check

```bash
curl http://localhost:8085/health
```

Expected: `{"status":"ok"}`

If that fails, wait 20 seconds and:

```bash
docker compose logs web --tail 50
```

You should see migrations, `Seed complete`, and `Starting website`.

Open `http://192.168.1.130:8085` and sign in with `ADMIN_USERNAME` / `ADMIN_PASSWORD` from `.env`.

---

## First use

The database is empty except for that login.

1. **People** — you, your girlfriend, her daughter.
2. **Platforms** — Nordea (bank), Nordnet (investment), anything else.
3. **Accounts** — each account on a platform; one owner or several if it is shared.
4. **Entries** — money in or out. Attach a PDF or photo. Add line items if you want.

---

## Later updates (folder already has the repo)

```bash
cd /mnt/user/appdata/receiptslegder
git pull
docker compose up -d --build
```

---

## Backup

```bash
cd /mnt/user/appdata/receiptslegder
docker compose exec db pg_dump -U receiptslegder receiptslegder > backup-$(date +%F).sql
```

Also copy `postgres/` and `documents/` if you used step 3.

---

## Troubleshooting

**502** — `web` is still migrating. `docker compose logs web --tail 50`, then retry.

**Login rejected** — use the username and password in `.env`, not an old password. Restart: `docker compose up -d`. Those values are written into the database when `web` starts.

**Port in use** — change `HTTP_PORT` in `.env` and run `docker compose up -d` again.
