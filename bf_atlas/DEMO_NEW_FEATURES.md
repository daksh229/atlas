# BF Atlas — Follow-up Video: What's New Since the First POC

> The first walkthrough showed the **screens** (alerts, brand maps, relationships,
> radar, catalog) on **mock data**. This video covers only **what changed since
> then** — so skip re-explaining the basic navigation and screens. The one-line
> framing to open with:
>
> *"Since the last video, two big things changed: Atlas now runs on **your real
> exported data**, not mock numbers — and we built the **offer evaluation** from
> the trial task. Let me show you just the new parts."*

**Setup before recording:** both servers running, open `http://localhost:5173`,
log in as a **data-rich trader (Daniel Okonkwo)**. Pre-open the Alerts page once
so the matching engine is warm. Target runtime: **~5–6 minutes**.

---

## 1 · It's on your real data now (~50s) — the headline

Open **Overview**. Point at the KPIs and the **provenance badges**.

> "First and biggest change — everything you're seeing is built from **your real
> files**: the product master, sales history, purchase history, the supplier
> offers, and the retailer prices. This trader has 63 real clients, 61 suppliers,
> €14M of real revenue. The first version was planted demo data; this is yours."

Then point at the three badges:
> "And we're explicit about provenance, because you told us only Odoo is solid
> today. **Orders and partners are real Odoo export. Demand is derived from your
> sales history** — since NetHunt isn't live yet. **Live stock is synthetic** for
> now. We label it in the product instead of pretending it's all real."

**Why it's new / why it matters:** directly answers his "how do you reason about
the uncertain sources" test, and proves we ingested the actual package — not a toy.

---

## 2 · The brand dictionary, at real scale (~60s) — his #1 risk

Open **Brands I Can Sell**, then click a brand (ideally one with messy spellings).

> "You called messy brand names the single biggest technical risk — and the first
> POC only had ~50 clean demo brands. We rebuilt this from **your real product
> master: 482 brands**. In your actual files, one brand shows up many ways —
> **'YSL', 'Saint Laurent', 'Yves Saint Laurent', 'Y.S.L.'**, and Tom Ford as
> **'TomFord'** and **'T. Ford'**. We resolve all of those to one canonical brand,
> automatically, including accents and noise like a stray ' Paris' on the end."

> "And when a brand genuinely isn't ours — we **flag it, we never force a match**.
> Get this layer wrong and the whole engine silently matches nothing. So it's the
> thing we built first."

**Why it's new:** 50 mock brands → 482 real, with real-world spelling chaos handled.

---

## 3 · Offer Evaluation — the trial task, live (~110s) — the centerpiece new screen

Open **Market Activity → Offer Evaluation**. This screen did **not** exist in the
first video. Give it the most time.

> "This is the new screen, and it's the exact problem from your trial task: a
> supplier sends an offer — messy format, mixed currencies — and a trader has
> about a minute to judge: is this worth pursuing, and who internally should know?"

Walk the tabs and a row:
> "We run it against all **three** of your real offer formats — the clean table,
> the messy broker list, the formal price list. Every line is joined to your data
> on the **EAN barcode** — the reliable key, because the names are chaos — and
> every price is converted to **euros at the ECB rate for that offer's date**."

Click a **Good** row, read the reasoning out loud:
> "Here — *31% below our average buy, around 80% resale headroom, and it's been
> sold before by these two traders.* So in one glance: good deal, and who to loop
> in. Green is good, amber borderline, red skip."

Switch to the **offer_1** tab:
> "And the honesty point again — most of this particular offer is product you've
> **never traded**. Instead of inventing a number, we flag it as 'no exact match'
> and give brand-level context. We never fake a match to look smart."

Point at the 'Clients' line in a row detail:
> "Notice we route to the responsible **trader**, but the client names are
> **masked** — even here, we don't expose another trader's accounts."

**Why it's new:** the whole offer-judgment capability (multi-format parsing, EAN
join, ECB currency, the verdict logic, who-should-know) is brand new and is the
paid-trial deliverable.

---

## 4 · The messy-data handling underneath (~40s) — credibility beat

Stay on Offer Evaluation or Overview; this is mostly narration.

> "A couple of things you won't see on screen but matter. Your order exports are
> 'flattened' — the salesperson and customer only appear on the first line of each
> order. If you don't handle that, you silently lose about **90% of who-did-what**.
> We fix it, so trader attribution is correct. And your data spans **four
> currencies** — euro, dollar, pound, yen — all normalised to euro before anything
> is compared. The mess in the files isn't an afterthought; we treated it as the
> actual problem."

**Why it's new:** demonstrates we engineered for *their* real data quality, not a
clean demo.

---

## 5 · The familiar screens — now real (~50s) — quick, don't dwell

Quickly click through, framing each as "same screen, now real":

- **Opportunity Alerts:** "Same alert engine you saw — but now firing on real
  signals. Reorder reminders, for example, are computed from your **actual order
  cadence and dates**, not a planted scenario."
- **My Clients / My Suppliers:** "Real accounts now, with real lifetime value and
  order history pulled from the exports."
- **Retailer Radar / Brand Catalog:** "Same as before — radar on your real retailer
  file, catalog now listing all 482 real brands."

> "I won't re-explain these — they're what you saw last time — just flagging that
> they're all running on your data now."

**Why it's new:** shows breadth carried over to real data without re-teaching.

---

## 6 · Access control, still server-side, now on real accounts (~30s)

Exit → re-onboard as a **second trader** (e.g. Sofia Romano).

> "And the non-negotiable still holds on real data: different trader, different
> clients, different alerts — and the accounts that were Daniel's now show masked.
> Enforced on the server, not hidden in the page."

**Why it's new:** proves the §9 rule survived the move to real, multi-trader data.

---

## 7 · Close (~30s)

> "So since the first video: it's on your real data, the brand dictionary is built
> from your 482 brands, currencies and barcodes are handled, and there's a working
> offer evaluation — the trial task — inside the same product. What's still ahead
> is the live Odoo connection, the production retailer scraper, and the Postgres/AWS
> deployment — we've scoped those honestly for the next phase. Happy to go line by
> line on any of it."

---

## New-vs-first-video cheat sheet (for your own reference)

| Shown in first video (skip) | New in this video (cover) |
|---|---|
| The 5 screens on **mock** data | Same screens on **real** data |
| ~50 demo brands | **482 real brands** + real spelling chaos |
| Masking concept | Masking **verified server-side on real accounts** |
| Offer **Inbox** (email parse) | **Offer Evaluation** screen (judge offer + verdict + routing) |
| — | **Multi-currency → EUR (ECB)** |
| — | **EAN-based matching** + unknown-flagging |
| — | **Data-quality handling** (flattened-export fix) |
| — | **Provenance badges** (real / derived / synthetic) |
| — | **Real LTV, order counts, reorder cadence** |

## Recording tips
- Pre-warm the Alerts page (first load runs the engine).
- If a screen looks empty, you're on a quiet trader — switch to Daniel / Sofia / Lucas.
- Keep the cursor slow; pause on each badge and verdict you mention.
