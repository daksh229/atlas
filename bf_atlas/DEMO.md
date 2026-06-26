# BF Atlas — Demo Walkthrough

A 10-minute click-through of the POC, mapped to the spec. Everything below runs on
planted data, so each step is reliable and repeatable.

## Before you start
```powershell
cd bf_atlas/data/pipeline; python build.py     # builds atlas.db (only needed once)
cd ../../backend; uvicorn app.main:app --reload --port 8000
cd ../frontend-react; npm run dev               # open http://localhost:5173
```
Two traders to know:
- **Sophie Laurent** — Team Aurora
- **David Chen** — Team Zenith

---

## 1 · It's an application, not a chatbot  *(spec §4)*
Open the app. Point out the **left-hand navigation** grouped into the spec's
sections — *My View, Brand Maps, My Relationships, Market Activity, System*.
There is no "ask a question" box anywhere; the trader navigates structured screens.

## 2 · Sign in as a trader  *(spec §9 — access control)*
Onboard as **Sophie Laurent**. The header shows "Signed in as Sophie Laurent ·
Team Aurora." Everything she sees is scoped to her own accounts — enforced on the
server, not hidden in the UI.

## 3 · Opportunity Alerts — the landing page  *(spec §6, §7, §9)*
This is her daily action list. Call out:
- Alerts are **routed to her** (right-person routing), **ranked by priority**, and
  **bundled by brand**.
- The **"Suppressed (daily cap)"** KPI — extra alerts held back so the feed never
  becomes spam (alert quality control).
- The alert types: **Demand–Supply, External Market Window, Stock Match, Reorder
  Reminder** (the 4 core), plus **Offer-to-Request** and **Triple Match**.
- On a Demand–Supply / Triple alert, the counterparty reads **"(via <colleague>)"** —
  another trader's client/supplier is **never named**, only the responsible colleague.

## 4 · Brand intelligence + the brand dictionary  *(spec §7, §9)*
Go to **Brand Maps → Brands I Can Sell**, click **Yves Saint Laurent**.
- The detail page shows **which colleagues** are active, **which clients** want it,
  **which retailers** carry it, and the **best historical sell price**.
- Rows she owns are tagged **"yours"**; rows she doesn't are **"masked"**.
- Mention the dictionary: this brand was matched even though the raw data spelled it
  "YSL" / "Saint Laurent" / "Yves Saint-Laurent" — one canonical brand, so matching
  never breaks on spelling.

## 5 · My Relationships  *(spec §8, §9)*
**My Clients** and **My Suppliers** list only Sophie's own accounts. (In step 8
we'll prove another trader sees a completely different set.)

## 6 · Offers Inbox — AI email parsing → match  *(spec §7 Phase 2)*
Go to **Market Activity → Offers Inbox**. This is the one place AI is visible.
1. Click the **"Weekly price list"** email and press **Extract offers**. Claude
   (Haiku) reads the free-text email and returns **5 structured offers** — and the
   brand dictionary resolves every messy spelling ("Dior", "D&G", "Lancome") to the
   right brand. The tag shows **"AI extracted"** (or "heuristic" with no API key).
2. Click the **"Two lines available"** email → the unknown brands (Mystère de
   Paris, Kayali) are **flagged, not force-matched**.
3. Press **Accept & match** on the price list → it records the offers and fires
   **Offer-to-Request Matches** against existing client demand, with margins.

There's also a **Quick-add** box (brand/price/qty) for the no-email path — try
**Chanel / 30 / 200** for an instant match.

> Honesty note: real email *ingestion* (IMAP/parsing infra) is still Phase 2; here
> the inbox is a folder of fixture emails. The **extraction is real AI**, the
> matching is real, and unknown brands are never faked.

## 7 · Retailer Radar  *(spec §5, §7 External Market Window)*
**Market Activity → Retailer Radar**. Each retailer row is matched to our supply
price via the brand dictionary; **"Market windows"** are where we can supply below
the retail price. Note the **one unknown brand** flagged at the bottom — the system
never invents a match.

## 8 · Prove the access control  *(spec §9 — the non-negotiable)*
Exit, re-onboard as **David Chen** (Team Zenith).
- His **Opportunity Alerts**, **My Clients**, and **My Suppliers** are a *different
  set* — he never sees Sophie's accounts by name.
- Open the same brand detail page: the rows that were "yours" for Sophie now show as
  "masked" for David, and vice-versa.

## 9 · Brand Catalog — the shareable output  *(spec §7)*
**System → Brand Catalog → Export PDF**. A clean, company-wide brand list with **no
internal data** (no prices, clients, suppliers or margins) — the "here's what we
distribute" hand-out.

---

## One-line recap for the client
> Atlas brings scattered signals — demand, supply, live stock, retail prices —
> together per brand, routes a short, de-duplicated list of real opportunities to the
> right trader, and never exposes another trader's accounts. All on the required
> stack, with the brand dictionary and trader-level access control built in.

## What's deliberately out of POC scope
Real read-only **Odoo / NetHunt** sync, **PostgreSQL**, **AWS (EU)**, Google OAuth,
production scrapers, and the email-parsing side of Offers. The data here is
**Odoo-shaped**, so those integrations slot in behind the same interfaces later.
