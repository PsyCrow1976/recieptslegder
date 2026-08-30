# Receipts Ledger

Personal ledger for Danish shop receipts. Photograph a till slip, read vendor / date / line items, check the total, tag the receipt as a project or group, and see spend in a calendar.

Iteration 1 is built around **Harald Nyborg** (thermal till receipts: `Varenr`, `Antal`, `Varetekst`, `Ialt`). Other Danish vendors can still be scanned as a generic fallback.

GitHub: [https://github.com/PsyCrow1976/recieptslegder](https://github.com/PsyCrow1976/recieptslegder)

## Features

- **Scan** — upload a JPEG/PNG; SpaceXAI vision + a Harald Nyborg normalizer extract SKU, qty, description, prices, store, date, invoice, VAT
- **Verify** — line sum vs `I ALT`, `Heraf moms` vs 25% inclusive VAT
- **Tags** — create / edit / delete projects or groups; many tags per receipt; spend by tag
- **Calendar** — month view of purchase dates
- **Product match** — Harald Nyborg `varenr` → [harald-nyborg.dk product page](https://www.harald-nyborg.dk/product/index?id=45359)
- **Dashboard** — this month, all time, vendor and tag totals

## Stack

PostgreSQL 16, FastAPI, React + Vite + Tailwind, nginx, Docker Compose.

Receipt scanning uses **SpaceXAI** (`XAI_API_KEY`, `https://api.x.ai/v1`, model `grok-4.6`).

## Unraid

See **[deploy.md](deploy.md)** for the full Unraid Docker Compose guide.

Short version:

```bash
mkdir -p /mnt/user/appdata/receiptslegder && cd /mnt/user/appdata/receiptslegder
git clone https://github.com/PsyCrow1976/recieptslegder.git .
cp .env.example .env && nano .env   # passwords + XAI_API_KEY
cp docker-compose.override.example.yml docker-compose.override.yml
docker compose up -d --build
```

Open [http://192.168.1.130:8085](http://192.168.1.130:8085).

## Local development

```bash
cp .env.example .env
# set XAI_API_KEY for live scanning
docker compose up -d --build
```

Open [http://localhost:8085](http://localhost:8085).

Parser tests (no Docker, no API key):

```bash
cd api
pip install -r requirements.txt
pytest
```

## Training receipts

`trainingreceipts/` contains six Harald Nyborg photos used as parser fixtures (Herlev, Maribo, Bladsaxe, August 2026).
