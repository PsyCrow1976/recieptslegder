# Changelog

All notable changes to Receipts Ledger are documented here.

## 0.1.0 — 2026-08-30

First version: a personal Danish receipt ledger for Unraid, with Harald Nyborg as the first vendor.

### Added

- Scan or upload a receipt photo. SpaceXAI (`grok-4.6` vision) reads the slip; a Harald Nyborg normalizer extracts vendor, store, date, `varenr`, quantity, description, line totals, `I ALT`, and `Heraf moms`.
- Total check: line items must add up to the printed total (1 øre tolerance). VAT is checked against 25% inclusive (moms = 20% of total).
- Review screen: original photo beside an editable line table. Confirm before the receipt is saved to the ledger.
- Tags (projects / groups): create, edit, and delete on the Tags page; attach several tags on a receipt; spend-by-tag overview.
- Calendar month view keyed off the receipt date.
- Dashboard: this month, all time, spend by tag and vendor.
- Harald Nyborg product lookup: `https://www.harald-nyborg.dk/product/index?id={varenr}` is fetched on save and via **Match products**, then linked on each line.
- Docker Compose stack (PostgreSQL 16, FastAPI, nginx + React) for Unraid, default port **8090**.
- Login with `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
- Training receipts under `trainingreceipts/` and golden parser tests for the six Harald Nyborg photos.
