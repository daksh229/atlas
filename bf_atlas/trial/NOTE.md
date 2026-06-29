# BF Atlas — Trial Note

*A supplier-offer evaluator: is this offer worth pursuing, why, and who internally should know?*

---

## What I built

A small tool that takes a supplier offer (in any of your three formats), joins it to BF's own
history on the **EAN**, normalizes every price to **EUR using ECB reference rates**, and shows a
trader — at a glance — which lines are worth attention, why, and which colleagues to loop in.

Pipeline: `ingest → normalize → evaluate → one JSON → one React screen`. No database, no login, no
deployment — deliberately. The intelligence is in `data/pipeline/` (pure, testable Python); the
screen just renders the result.

Run: `python -m data.pipeline.build_offers`, then `cd trial/web && npm install && npm run dev`.

---

## The main choices I made (and why)

**EAN is the join; brand names are only a fallback.** Product names in the offers are unusable as a
key — one brand appears as `Hermès Paris`, `Hermès`, `Y.S.L.`, `yves saint laurent`, `TomFord`,
`T. Ford`. So every verdict is driven by the EAN. I still built a 482-brand dictionary (from
`Products_Info`, not a hardcoded list) with a normalizer that handles accents, punctuation,
initialisms (`Y.S.L.`→`ysl`), doubled prefixes (`Electimuss Electimuss London`), and the noise
suffixes your retailer data carries (`Sisley Paris`, `Wella Paris`). But the brand name is used for
*display and fallback*, never to assert a per-product verdict.

**The highest-impact fix was unglamorous: the flattened export.** In both order histories,
`Salesperson`/`Customer`/`Date` (and `Buyer`/`Vendor`) appear only on the *first* line of each
order and are blank on every continuation line. Forward-filling them took trader attribution from
~10% to 100%. Without it, the "who should know" half of the task is silently broken — and it would
have *looked* like it worked. This is the kind of quiet data-quality trap I'd expect a lot of the
real project to be made of.

**Multi-currency, done properly.** Your files span EUR/USD/GBP/JPY. I convert at the **row's own
date** using the full ECB history (e.g. a 2024-12-15 USD offer uses the 2024-12-13 rate, since the
15th was a weekend), not a single "today" rate. Rates are cached locally with an offline fallback so
a build is reproducible and never hard-fails on a network blip.

**Honest non-matches.** When an EAN isn't in BF's catalog, I do **not** force a match. I fall back to
clearly-labelled brand-level *context* ("no exact match; at brand level BF buys ~€64 / sells ~€77
across 179 Tom Ford products") and route to the colleagues who work that brand — but it is never
presented as a per-product verdict.

**Access control, even here.** The tool has no login (per the brief), so there's nobody to mask
against. But the spec is firm that client/vendor *account names* are sensitive, so the "who should
know" output routes to the responsible **trader** and shows clients only as a masked count — it
never prints a client's name.

---

## How I decided whether an offer is good

You deliberately gave no target margin, so I made the reasoning explicit and tunable rather than
hiding a magic number. For each line (in EUR):

1. **Cost** — compare the offered price to what BF usually pays: the product's average and minimum
   purchase price, cross-checked against real purchase history. At or below our average buy is
   attractive; below our best-ever buy is strong.
2. **Resale headroom** — margin against the **conservative** of {our average sale price, the live
   market price}. I take the lower of the two on purpose: it's the defensible floor, and the retailer
   sample is thin, so I'd rather under-promise than inflate a deal on sparse market data.
3. **Verdict** — *good* when it's below our average buy **and** clears a healthy headroom band;
   *borderline* / *skip* below that; *unknown* when we have no basis to judge.

The bands (25% / 10%) and the price bases live in one config file and are surfaced in the UI, so the
threshold is a business conversation, not a buried constant. Example output:
*"€13.50 (15.31 USD) — 31% below our avg buy €19.48; ~83% resale headroom; sold before by Aisha
Rahman, Lucas Moreau"* → ranked by potential € value (margin × quantity).

**A real finding worth flagging:** offer_1 is almost entirely product BF has never traded — only 4
of its 31 EANs exist in your catalog. The tool says so plainly rather than inventing benchmarks.
That's a feature, not a gap: a trader should know immediately when our history can't speak to an
offer.

---

## What I deliberately did NOT do

- **No platform features** — no alerts engine, brand maps, retailer radar, catalog PDF, nightly job.
  Those are the full spec, not this task. Doing them here would be doing more, badly.
- **No fuzzy name matching for verdicts.** EAN-only for any actual good/bad call. Name matching is
  too risky to base a buy decision on; I kept it to display + brand-level context.
- **No size/pack reconciliation beyond the EAN.** The EAN already encodes the specific size, so
  EAN-matched lines are size-correct; I parse volume for display but don't use it to force matches.
- **No live retailer scraping** — I used your sample file (the approach is below).
- **No database / auth / deployment** — a precomputed JSON and a single screen are enough to show
  the analysis, which is what's being judged.

---

## Pulling retailer prices from real sites, at scale

For the trial I used the sample file. In production this is its own subsystem, and the hard parts
aren't the happy path:

- **Per-retailer adapters, not one scraper.** Douglas, Notino, ICI Paris XL, De Bijenkorf, Etos,
  Kruidvat each have different markup; some need a headless browser, some expose a JSON API. I'd
  build small adapters behind one interface, scheduled independently.
- **Matching scraped rows back to our EANs is the real problem.** Retailer pages often *don't* show
  the EAN, so you're matching on brand + product name + size — exactly the messy join the brief warns
  about. I'd resolve via the brand dictionary + size normalization and keep a confidence score, and
  flag low-confidence matches rather than trusting them.
- **Reliability & currency:** rate-limiting and politeness (robots.txt, ToS, off-peak scheduling),
  resilience to layout changes (selectors break constantly — monitor match-rate and alert on drops),
  anti-bot handling, per-country currency/locale, and outlier filtering (a broken scrape that reads
  €3 for a €130 perfume must never reach the matching engine).
- **Freshness vs cost:** a nightly scan for breadth, with targeted refreshes for brands that have an
  active offer in play. Store every price with its scan date and source so staleness is visible.

The legal/ToS posture matters here and is a decision for BF, not me to assume — I'd want to agree the
boundaries before scaling this.

---

## Where the real Atlas will be harder than this suggests

- **Live Odoo, not a file.** Read-only JSON-RPC, the custom **Trade** model and **Matched %**, live
  stock lots, confirmation-date-accurate margins — and doing it incrementally at full corpus size
  (your exports are already ~130k lines; production is bigger). The pipeline is written to vectorize
  and push work into SQL for exactly this, but a real Odoo feed is a project in itself.
- **Access control for real.** Reusing Odoo's record rules so masking is enforced server-side for 24
  traders across 5 teams, on every response — not the single-view simplification here.
- **Alert quality at scale.** With hundreds of accounts, the matching engine can generate hundreds of
  alerts/day. Dedup, bundle-by-brand, daily caps, right-person routing, and not re-firing — the
  "don't become spam" rules — are as important as the matching itself.
- **The retailer scanning subsystem** (above) is genuinely the riskiest external dependency.
- **Undefined inputs:** NetHunt demand signals are "to be defined"; dangerous goods, decoding, and
  extra labour costs all affect true margin. The brand dictionary is clean in Odoo but will be messy
  on retailer sites.

---

## Reflection

This task told me Atlas is, at its core, a **pre-deal radar**: its value is connecting traders and
giving them an honest read *before* anything enters Odoo. The interesting engineering is not the UI —
it's the data normalization and the discipline to never fake a match. The product wins or loses on
trust: a trader will use it daily only if, when it says "good," it's right, and when it doesn't know,
it says so. So the most important thing I did was make the reasoning transparent and the unknowns
loud.

**Questions I'd want to ask if the real project started tomorrow:**
- Is there a working **target margin** (or per-category bands), or do you genuinely want the system to
  reason without one? What we choose here shapes every verdict.
- For the "market check," which retailers are **authoritative** per brand/region, and how *current*
  must that price be to be trusted?
- How available is the **EAN on retailer sites** in practice — is name+size matching the real norm?
- Can Atlas read the **Trade / Matched %** fields under the access rules? Those look like the single
  strongest open-opportunity signal.
- What's the real **volume of offers per day** per trader, and how fast must a verdict come back?
- The **Alert Engine Spec** (thresholds, lifecycle) is under NDA — I'd want it early, since it
  encodes the business logic the four core alerts depend on.

Good questions, I think, tell you as much as the code does — and these are the ones whose answers
would most change how I'd build it.
