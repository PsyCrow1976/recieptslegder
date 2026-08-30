# Deploy Receipts Ledger on Unraid (Docker Compose)

Step-by-step install on Unraid. This matches the same pattern as FitLineVentory on the same server.

**Your server:** `192.168.1.130`  
**App URL after install:** `http://192.168.1.130:8085`

Port **8085** is used so this stack does not collide with FitLineVentory on **8080**.

---

## What gets installed

Docker Compose starts three containers:

| Container | Role |
|-----------|------|
| `db` | PostgreSQL 16 — receipts, tags, products |
| `api` | FastAPI — OCR, ledger, product lookup |
| `web` | nginx — web UI + API proxy on port `8085` |

Receipt **photos** are stored on a Docker volume (or Unraid appdata if you use the override file).

Scanning uses **Tesseract inside the API container** (Danish + English). No cloud OCR and no API key.

---

## Prerequisites

1. **Docker is running** — Unraid → **Settings → Docker** → enabled.
2. **Docker Compose** — Unraid does not ship with `docker compose`. See **Step 0**.
3. **Git** — `git --version`. Install from **Apps** (Nerd Tools / git) if missing.
4. **Port 8085 is free** — or set `HTTP_PORT` in `.env`.
5. Terminal or SSH:
   ```bash
   ssh root@192.168.1.130
   ```


### Check what you have

```bash
docker version
docker compose version
docker-compose version
```

| Output | Meaning |
|--------|---------|
| `docker compose version` shows v2.x | Ready — skip to Step 1 |
| `unknown command` / `not found` for compose | Install Step 0 first |
| Only `docker-compose` (hyphen) works | Use `docker-compose` in all commands below |

---

## Step 0 — Install Docker Compose on Unraid

### Method A — Compose Manager Plus (recommended)

1. Unraid → **Apps**
2. Search **Compose Manager Plus**
3. **Install**
4. Verify:
   ```bash
   docker compose version
   ```

**Manual plugin URL** if Apps search fails:

```
https://raw.githubusercontent.com/mstrhakr/compose_plugin/main/compose.manager.plg
```

Unraid → **Plugins** → **Install Plugin** → paste that URL.

### Method B — Legacy Docker Compose Manager

**Apps** → search **Docker Compose Manager** → install, then try `docker compose version` or `docker-compose version`.

---

## Step 1 — Create the app folder

```bash
mkdir -p /mnt/user/appdata/receiptslegder
cd /mnt/user/appdata/receiptslegder
```

---

## Step 2 — Clone the repository

```bash
git clone https://github.com/PsyCrow1976/recieptslegder.git .
```

If the folder is not empty:

```bash
git clone https://github.com/PsyCrow1976/recieptslegder.git receiptslegder
cd receiptslegder
```

Confirm:

```bash
ls docker-compose.yml .env.example README.md
```

---

## Step 3 — Create and edit `.env`

```bash
cp .env.example .env
nano .env
```

**Change at least:**

| Variable | Notes |
|----------|--------|
| `POSTGRES_PASSWORD` | Strong password; must match the password in `DATABASE_URL` |
| `JWT_SECRET` | Long random string for login tokens |
| `ADMIN_PASSWORD` | Web login password |

Example:

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

The password in `DATABASE_URL` **must** be the same as `POSTGRES_PASSWORD`.

Save: `Ctrl+O`, Enter, `Ctrl+X` in nano.

---

## Step 4 — (Recommended) Store data on appdata

```bash
mkdir -p /mnt/user/appdata/receiptslegder/postgres
mkdir -p /mnt/user/appdata/receiptslegder/receipts
cp docker-compose.override.example.yml docker-compose.override.yml
```

This bind-mounts Postgres and receipt images to Unraid appdata so backups are obvious.

---

## Step 5A — Build and start (terminal)

```bash
cd /mnt/user/appdata/receiptslegder
docker compose up -d --build
```

Hyphenated fallback:

```bash
docker-compose up -d --build
```

First build can take several minutes.

```bash
docker compose ps
```

All three services should be **Up**, and `db` **healthy**.

---

## Step 5B — Build and start (Unraid web UI)

1. Finish Steps 1–4.
2. Unraid → **Plugins** → **Compose.Manager** (or Compose tab).
3. **Add New Stack** → name it `receiptslegder`.
4. Gear icon → **Edit Stack** → **Settings**:
   - External Compose Path: `/mnt/user/appdata/receiptslegder/docker-compose.yml`
   - External Env Path: `/mnt/user/appdata/receiptslegder/.env`
5. Gear icon → **Compose Up** / **Build & Up**.
6. Docker tab should show `receiptslegder-db-1`, `receiptslegder-api-1`, `receiptslegder-web-1`.

---

## Step 6 — Verify

```bash
curl http://localhost:8085/health
```

Expected: `{"status":"ok"}`

Login (use your `ADMIN_PASSWORD`):

```bash
curl -X POST http://localhost:8085/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_ADMIN_PASSWORD"}'
```

Expected: JSON with `access_token`.

On the LAN:

```
http://192.168.1.130:8085
```

Sign in with `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

API docs: `http://192.168.1.130:8085/docs`

---

## Step 7 — First use

1. **Tags** — create projects/groups (for example Sommerhus, Malerarbejde).
2. **Upload** — take a photo of a Harald Nyborg receipt (or use the training photos).
3. Review the line items, confirm the total, attach tags, **Confirm and save**.
4. **Match products** (or wait for auto-lookup) to open the item on harald-nyborg.dk.
5. **Calendar** — jump to the purchase date.
6. **Dashboard** — totals by tag and vendor.

---

## Start on boot

Containers use `restart: unless-stopped`, so they come back when Docker starts after an Unraid reboot.

---

## Updating

```bash
cd /mnt/user/appdata/receiptslegder
git pull
docker compose up -d --build
```

Database migrations run when the API container starts.

---

## Backup and restore

```bash
cd /mnt/user/appdata/receiptslegder
docker compose exec db pg_dump -U receiptslegder receiptslegder > backup-$(date +%F).sql
```

If you used Step 4, also back up:

- `/mnt/user/appdata/receiptslegder/postgres`
- `/mnt/user/appdata/receiptslegder/receipts`

Restore:

```bash
cat backup-2026-08-30.sql | docker compose exec -T db psql -U receiptslegder receiptslegder
```

---

## Useful commands

| Task | Command |
|------|---------|
| Logs | `docker compose logs -f` |
| API logs | `docker compose logs -f api` |
| Stop | `docker compose down` |
| Stop and delete DB volume | `docker compose down -v` ⚠️ deletes data |
| Rebuild | `docker compose up -d --build` |

---

## Troubleshooting

### Scan reads little or nothing

Crumpled thermal photos are hard for Tesseract. Correct the vendor and lines on the review page, then confirm. Failed reads stay in **Training** so we can teach new layouts later.

Rebuild after pulling this version (`tesseract-ocr-dan` is now in the API image):

```bash
docker compose up -d --build
```

### 502 Bad Gateway

API may still be migrating. Wait 30 seconds, then:

```bash
docker compose logs api --tail 50
docker compose restart api
```

### Cannot open `http://192.168.1.130:8085`

- `docker compose ps`
- `curl http://localhost:8085/health`
- Change `HTTP_PORT` in `.env` if 8085 is taken, and add the new URL to `CORS_ORIGINS`

### Login fails after changing `ADMIN_PASSWORD`

The admin user is created on **first startup**. Recreate after `.env` changes, or reset the database (`docker compose down -v` wipes data).

### `docker compose` not found

Install Compose Manager Plus (Step 0) or use Step 5B.

---

## Uninstall

```bash
cd /mnt/user/appdata/receiptslegder
docker compose down -v
rm -rf /mnt/user/appdata/receiptslegder
```

---

## Quick reference

| Item | Value |
|------|-------|
| Project path | `/mnt/user/appdata/receiptslegder` |
| Web UI | `http://192.168.1.130:8085` |
| API | `http://192.168.1.130:8085/api/v1` |
| Docs | `http://192.168.1.130:8085/docs` |
| GitHub | https://github.com/PsyCrow1976/recieptslegder |
