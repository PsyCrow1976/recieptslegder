# Local OCR — adaptable scanner and training studio

Plan for a later feature. **Not implemented yet.** Scanning today is Tesseract plus a Harald Nyborg whole-line regex (`api/app/services/ocr.py`, `hn_layout.py`). That misses line items on the photos in `trainingreceipts/`.

Stay **fully local**. No cloud vision API.

---

## Problem

Harald Nyborg till slips are a stable four-column layout:

`Varenr | Antal | Varetekst | Ialt`

The photos are crumpled, skewed, and low-contrast. The current pipeline:

1. Preprocess (scale, grayscale, contrast).
2. Run Tesseract `image_to_data`.
3. **Drop bounding boxes** and glue words into lines by Y overlap.
4. Require **one reconstructed line** to match SKU + qty + description + amount.

That last step is why items disappear:

| What happens | Result |
|--------------|--------|
| One printed row becomes two OCR lines (SKU on one, `28,00` on the next) | Regex never matches |
| Amount is not at the end of the joined line | Price is ignored |
| Tokens with Tesseract `conf < 0` are dropped | SKU or price never appears |
| Skip-words (`dato`, `ialt`, …) are too aggressive | Real item lines skipped |
| Only Harald Nyborg has a layout | Other vendors get empty lines and `needs_training` |
| Corrections on the review page are not written back | The parser never learns |

`needs_training` already flags failures and `raw_parse.ocr_text` is stored, but there is no way to label boxes or save a vendor layout.

---

## Goal

A **custom in-app training interface** so you teach the scanner, on your Unraid box:

- which tokens are **vendor / store / date / total / moms**
- which tokens are **item number, description, quantity, line price**
- how those sit **in space** on that vendor’s slip (columns and bands)

After you label one (or a few) receipts for a vendor, later slips from the same chain use that layout. A new vendor starts as a blank layout you train the same way.

**Acceptance for the six training photos:** after labeling **one** Harald Nyborg example, the other five recover **all** line items (item number, description, line price) and the printed **I ALT**, using the existing 1-øre total check.

---

## Approach: train layouts, not a new OCR engine

Do not start by retraining Tesseract’s neural model. That needs a large labeled corpus and is a poor fit for a home Unraid app.

Keep Tesseract as the **character reader**. Teach a **layout model** on top of word boxes:

```
photo
  → preprocess (optionally several variants)
  → Tesseract word boxes (text, x, y, w, h, confidence)
  → vendor guess (name, CVR, saved logo region)
  → apply that vendor’s column bands
  → candidate lines: SKU in the left band + amount in the right band
    even when OCR split them onto two Y-lines
  → review / training UI
  → your assignments become a labeled example
  → column bands and token hints update for that vendor
```

Word boxes are first-class data. The photo overlay is the training UI.

---

## Training studio (UI)

New page, opened from today’s **Training** queue (and from any receipt).

**Left:** original photo with zoom and pan.  
**Right:** structured fields (vendor, date, line items, total) — same ideas as the review page, bound to boxes on the image.

| Action | What it teaches |
|--------|-----------------|
| Word overlay | Each Tesseract word is a rectangle; colour = role (unassigned, SKU, description, price, total, …) |
| Click a box → assign role | `item_number`, `quantity`, `description`, `line_price`, `receipt_total`, `vat`, `date`, `vendor`, `ignore` |
| Shift-click / drag several boxes | Split descriptions, or `I A L T` plus the amount, become one field |
| Column rulers | Vertical guides as **% of receipt width**. Harald Nyborg starting guess: ~0–12% SKU, 12–20% qty, 20–78% text, 78–100% amount. Drag once; save on the vendor. |
| Header / footer bands | Horizontal guides so “I ALT” and return-policy text are not parsed as items |
| Link row | Boxes that belong to the same printed row become one line item even if OCR split them |
| Save layout | Writes the vendor’s column bands and token hints |
| Save example | Stores this receipt as a golden sample (image + boxes + labels) for regression tests |

**First-run Harald Nyborg:** open one training photo, place the four column guides, label the total line, save layout. Re-run parse on the other five without more labeling.

**New vendor later:** same studio, empty rulers, label one slip, save as that vendor’s layout.

---

## Data (when implemented)

- `receipts.ocr_words` (JSONB) — Tesseract boxes plus assigned roles  
- `vendor_layouts` — per-vendor column % bands, header/footer %, token hints (CVR, “I ALT”, “Varenr”)  
- `ocr_examples` — labeled receipts used as tests (`trainingreceipts/` seeded)

Parser change: **band assignment before regex**. Words in the right band that look like `29,50` are prices; the nearest unmatched SKU in the left band with a similar Y is the same line. That is what recovers split rows.

Optional later (not the first slice): extra preprocess (deskew, adaptive threshold, Tesseract PSM 4 vs 6 vs 11) and keep the variant whose line sum matches the printed total.

---

## Out of scope for the first slice of this feature

- Cloud vision  
- Training a new neural OCR from scratch  
- Handwritten receipts  
- Using the Harald Nyborg website as a substitute for reading the slip  

Optional product lookup on harald-nyborg.dk stays a separate button.

---

## Suggested implementation order (later session)

1. Persist Tesseract word boxes on scan (`ocr_words`), not only joined text.  
2. Training studio overlay + role assignment + save.  
3. `vendor_layouts` + column rulers; seed Harald Nyborg from one labeled training photo.  
4. Band-based line assembler (SKU left + price right, Y-tolerant).  
5. Re-parse the six training receipts; add golden tests from labeled examples.  
6. New vendor: create layout from a blank studio session.

---

## Current hooks already in the app

- Flag `needs_training` on failed scans  
- Training queue at `/receipts?training=1`  
- Review page to correct vendor and lines before confirm  
- `raw_parse.ocr_text` stored on the receipt  

The studio should reuse those; it adds boxes, layouts, and a feedback loop the regex parser does not have.
