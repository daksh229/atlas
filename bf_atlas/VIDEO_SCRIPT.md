# BF Atlas — POC Walkthrough · Video Script

**Audience:** B Futurist (business + technical) · **Target length:** ~8–9 min
**Format:** ***bold-italic = what to do on screen*** · plain bullets = what to say (first person)
**Before recording:** backend running (`uvicorn app.main:app`), frontend open, logged out (on the onboarding screen). Have the **brand-dictionary** point ready. Two traders to use: **Sophie Laurent** (Team Aurora) and **David Chen** (Team Zenith).

---

## 0 · Intro — what this is *(~45 sec)*

***[Start on the onboarding / login screen. Don't click yet.]***

- "This is **BF Atlas** — the first application of the BF Hub. It's an internal tool for your 24 traders that brings scattered information together and surfaces real trading opportunities."
- "Two things I want you to keep in mind as I go. **First — this is a navigable web application, not a chatbot.** Traders click through structured screens; they don't type questions to an AI."
- "**Second — AI does work underneath the product**, but it works on the *inputs* — reading messy supplier emails, scanning retailer prices — while the actual decisions about matches and access stay exact and rule-based. I'll show you exactly where the AI is."
- "Everything you'll see runs on sample data today. At the end I'll explain, in one section, where every piece of this data comes from in production — Odoo, NetHunt, and so on."

---

## 1 · Logging in — trader identity *(~30 sec)*

***[Click "Sophie Laurent" (Team Aurora), then "Enter Atlas".]***

- "A trader signs in as themselves. I'm signing in as **Sophie Laurent**."
- "From this moment, everything Sophie sees is **scoped to her** — her clients, her suppliers, her alerts. This isn't just hidden in the screen; it's enforced on the server. I'll prove that near the end by logging in as a different trader."

---

## 2 · Opportunity Alerts — the heart of the product *(~90 sec)*

***[You land on Opportunity Alerts. Point to the four cards at the top, then the alert list.]***

- "This is Sophie's landing page and the reason Atlas exists — her **daily action list of opportunities**, ranked by priority."
- "Atlas is a **matching engine**. For every brand it asks: *which signals fired recently?* — a client wanting it, a colleague who can supply it, stock we're holding, a retailer's price. When those line up, that's an opportunity."
- ***[Point to the "Suppressed (daily cap)" card.]*** "Critically, it's **not noisy**. Alerts are bundled by brand, ranked, de-duplicated, and capped per day. This 'suppressed' number is alerts we deliberately held back so the feed stays useful. A tool that fires 200 alerts a day gets ignored — this one won't."
- ***[Point to a Demand–Supply or Triple Match alert that says "(via …)".]*** "Here's the access rule in action. This match involves another trader. Sophie can see *which colleague* to go talk to — but she can **never see that colleague's client or supplier by name**. She sees the opportunity and the numbers, not the relationship."
- "Each alert type maps to a real trading situation: a demand–supply match, a retailer price window, stock we can move fast, and reorder reminders."

---

## 3 · Brand Maps + Brand Intelligence *(~75 sec)*

***[Open "Brands I Can Sell" in the left nav. Then click any brand row — e.g. Yves Saint Laurent.]***

- "Traders can also work **proactively**. 'Brands I Can Sell' is Sophie's universe of brands where her clients show demand; there's a matching 'Brands I Can Buy'."
- ***[Now on the brand detail page.]*** "Clicking any brand opens its full intelligence in one place — which colleagues are active on it, which clients want it, which retailers carry it, and the best historical price."
- ***[Point to a "yours" tag and a "masked" tag.]*** "Same privacy rule everywhere: rows Sophie owns are shown in full; rows that belong to another trader are **masked**."
- ***[Emphasise this — it's the strongest technical point.]*** "And here's something invisible but foundational. In the raw data, this brand was written as 'YSL', 'Saint Laurent', and 'Yves Saint-Laurent'. To a computer those look like three different brands — and the matching engine would silently miss deals. Atlas runs a **brand dictionary** that collapses every spelling into one canonical brand. Your spec calls this the biggest technical risk; it's built in from the ground up."

---

## 4 · My Relationships *(~30 sec)*

***[Open "My Clients", then "My Suppliers".]***

- "These are simply Sophie's **own** accounts — her clients and her suppliers, with order history and value."
- "Nothing here belongs to another trader. When I switch users later, these lists will be completely different people — that's the proof the wall is real."

---

## 5 · Offers Inbox — where the AI is *(~110 sec)*

***[Open "Offers Inbox" under Market Activity. Click the "Weekly price list" email.]***

- "This is the one place AI is visible. Suppliers send offers as **free-text emails** all day. Reading those by hand and turning them into structured data is exactly what AI is good at."
- ***[The email text shows. Click "Extract offers".]*** "I open a supplier's email and press extract. The AI reads it and pulls out **structured offers** — brand, price, quantity — and you can see it tagged 'AI extracted'."
- ***[Point to the extracted rows.]*** "Notice the email wrote 'Dior', 'D&G', 'Lancome' — and the **brand dictionary** has already resolved each one to the correct canonical brand. The AI reads; the deterministic dictionary decides."
- ***[Open the "Two lines available" email and extract.]*** "And it's honest. This email has brands we don't recognise — they're **flagged, not force-matched**. Atlas never invents a deal."
- ***[Go back to the price-list email, press "Accept & match".]*** "When the trader accepts, those offers run straight through the **same matching engine** — and here, they fire **Offer-to-Request matches** against clients who already want those brands, with the margin on each. The right traders get notified."
- "So the AI's job is to clean the input. The match, the margin, and who gets told — all of that stays exact and auditable."

---

## 6 · Retailer Radar + Brand Catalog *(~70 sec)*

***[Open "Retailer Radar".]***

- "Retailer Radar compares public retailer prices to what we can supply for, and flags the **market windows** — where a shop is selling high and we can come in below. Unknown brands are flagged here too, never guessed."
- ***[Data flow — say this while pointing at the rows.]*** "Where does this data come from? Today these rows are sample data sitting in our database. **In production, a scraper runs on a schedule, visits the retailer websites, and writes the brand, price, and stock straight into Atlas** — and every row is matched back to our catalogue through the **brand dictionary**, so a shop writing 'Dior' still lines up with our 'Christian Dior'. The AI helps read messy retailer pages; the price comparison itself stays exact."

***[Open "Brand Catalog", then click "Export PDF".]***

- "And the Brand Catalog is the one screen meant to leave the building — a clean, company-wide list of every brand we move, exportable as a PDF to hand a new client or supplier. It has brand names only — **no prices, no clients, no margins** — so it's safe to share."
- ***[Data flow — say this as the PDF downloads.]*** "This brand list is sample data today. **In production it comes straight from your Odoo product catalogue, read-only** — every brand BF distributes — and it's de-duplicated through the brand dictionary so each brand appears exactly once, no matter how many ways it was spelled in Odoo. Nothing internal is ever added; it's deliberately just the public brand names."

---

## 7 · The access-control proof *(~50 sec)*

***[Click Exit. Log back in as "David Chen" (Team Zenith).]***

- "This is the most important rule in your spec, so let me prove it rather than just claim it. I'm logging out of Sophie and in as **David Chen**, on a different team."
- ***[Open Opportunity Alerts, then My Clients.]*** "Completely different alerts. Completely different clients. David never sees Sophie's accounts."
- ***[Open the same brand detail page you showed earlier — e.g. YSL.]*** "And on the exact same brand page, the rows that were 'yours' for Sophie are now 'masked' for David, and vice versa. Same data, different viewer — each trader is sealed off from the others, enforced on the server."

---

## 8 · How the data flows — POC today vs production *(~110 sec)*

***[Optional: switch to a simple architecture slide/diagram, or just talk over the app.]***

- "Everything I showed runs on **sample data in a single database** today. Let me explain where each piece comes from when this goes to production — because that's the real engineering."
- "**Odoo is the foundation.** It's your ERP and the stable source of truth. In production, Atlas reads — **read-only, one direction** — your products, brands, live stock, purchase orders, sales orders, and your client and supplier accounts from Odoo. Atlas never writes back to Odoo."
- "**NetHunt, your CRM**, feeds the forward-looking side — what clients are *asking* for. That's the demand signal behind 'Brands I Can Sell' and the demand–supply matches."
- "**Retailer websites** are scanned by a scraper that writes prices into Atlas — that powers Retailer Radar and the market-window alerts."
- "**Supplier emails** flow through the AI parser I just showed — that becomes the supply side and the Offer-to-Request matches."
- "Sitting under all four is the **brand dictionary** — the canonicalisation layer that makes sure every source agrees on what a brand *is*, so matching never breaks on spelling."
- "To prove this path is real, even in the POC we built a small **preprocessing pipeline**: raw, messy data comes in, gets canonicalised through the dictionary, and is loaded into clean tables — which is exactly the shape the Odoo and NetHunt feeds will plug into."
- "And to be transparent about the POC boundary: today it's **SQLite** standing in for PostgreSQL, there's no live Odoo or NetHunt connection yet, and the retailer and email *ingestion* is simulated — but the **logic, the screens, the matching, the access control, and the AI extraction are all real**."
- "The stack is exactly what your spec asks for: **FastAPI, React with TypeScript and Tailwind, PostgreSQL, on AWS in the EU**."

---

## 9 · Close *(~25 sec)*

- "So that's BF Atlas: a navigable application — not a chatbot — that pulls demand, supply, stock, and retail prices together per brand, routes a short, de-duplicated list of real opportunities to the right trader, and never exposes one trader's accounts to another."
- "The four core alerts, the access control, and the brand dictionary — the foundation of your Phase 1 — are all working here. The next step is wiring it to the live Odoo and NetHunt feeds and moving it onto your production stack."
- "Happy to go deeper on any screen or on the integration plan."

---

### Quick reference — running order
Login (Sophie) → Opportunity Alerts → Brands I Can Sell → Brand detail (dictionary) → My Clients/Suppliers → **Offers Inbox (AI)** → Retailer Radar → Brand Catalog (PDF) → re-login (David, access proof) → **Data-flow section** → close.

*Est. total spoken time: ~8.5 min (excludes click/transition pauses).*
