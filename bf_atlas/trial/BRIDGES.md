# Bridges, not silos — building the BF Hub, not a pile of apps

*A short view on how I'd keep Atlas, the HR recognition app, and whatever comes next a connected
platform rather than disconnected tools. Thinking, not code.*

---

## Technical architecture: build once, vary deliberately

The trap is obvious in hindsight: each app reaches into Odoo and Google on its own, reinvents login
and access control, and ends up a silo (the HR app already lives in a separate Google environment —
that's silo #1 forming). The fix isn't a giant platform up front; it's a **thin shared spine** that
every app sits on, with everything else owned by the app.

**Build once (the BF Hub spine):**
- **One Odoo integration layer.** A single read-only connector and a set of canonical, normalized
  models (products/EAN, brands, partners, trades, prices). Apps consume *these*, never raw Odoo.
  This is also where the brand dictionary, EAN cleaning, and FX/currency normalization live — Atlas
  needs them now, the next trading-adjacent app will too.
- **One identity + access-control service.** Google SSO for login, and access rules sourced from
  Odoo's existing record rules so "a trader sees only their accounts" is enforced once, server-side,
  for every app — not re-implemented (and re-bugged) per app.
- **One governed data layer.** Odoo stays the system of record; a governed integration/warehouse
  layer holds the normalized copy apps read, with clear schemas, ownership, lineage, and a catalog.
  Google Workspace data (the HR app's forms, nominations) flows into the *same* governed layer
  through Workspace APIs — so HR and trading data are consistent and discoverable, not trapped in one
  app's database.
- **One shared AI service.** A single place that wraps LLM calls (offer parsing, retailer scanning,
  the HR app's nomination-validation check). Same guardrails, same cost controls, same logging.
- **One platform: deploy/infra/observability.** AWS EU region, CI/CD, monitoring, a shared UI
  component library so the apps feel like one product.

**Vary per app (the actual product):** the domain models and logic (a supplier offer vs a
recognition nomination), the screens, and the app-specific workflows (Atlas's matching/alerts; HR's
form → admin approval → AI criteria check). These *should* differ — that's the point of one app per
department.

**A discipline I'd hold to:** don't build the shared platform speculatively. Build Atlas well, then
**extract** the spine when the second app (HR) needs the same thing. You earn the abstraction from
two real cases, not from a diagram. Over-platforming before app #2 is how you get a slow, wrong
foundation.

**Where it runs and how it stays governed while still moving fast:** all apps as services behind one
portal (the Hub) on shared AWS-EU infra, behind a shared auth gateway. Governance comes from funneling
every source through the shared integration layer (so there's one place to enforce access, GDPR, and
data quality) — not from a heavyweight process. Apps move fast because they only own their slice;
the platform team owns the spine as an internal product with stable contracts.

---

## Change management: adopted, trusted, and yours to run

Technology is the easy half. These tools succeed only if people use them, trust them, and BF can run
them without us.

**Adoption — solve a real daily pain, with the people who feel it.** Atlas's whole reason to exist is
the one-minute "is this offer good?" judgment traders do today in spreadsheets. I'd co-design with a
couple of trader power-users, ship a thin version into their real workflow early, watch actual usage,
and iterate. A tool imposed top-down dies; one shaped by its users gets defended by them.

**Trust — transparency over cleverness.** A trader trusts a recommendation only if they can see the
numbers behind it and the system is honest when it doesn't know. That's why the evaluator shows its
cost/headroom reasoning and flags non-matches instead of faking them. Trust, once lost to a confident
wrong answer, doesn't come back — so I'd bias every design toward "show your work."

**Self-sufficiency — design for handover from day one.** The brief is explicit that BF wants to run
and improve these tools after we step back. That means: a standard, boring, well-documented stack (no
clever magic that only the author understands); pure, tested core logic; runbooks; and pairing with
BF's team on real extensions during the build, not a doc dump at the end. The goal is that BF can
add the third app mostly themselves.

**Process & governance — evolve it lightly.** A small platform team owning the spine; clear data
ownership; a thin review process for new apps so they reuse the spine instead of forking it; and
deliberately folding shadow tools back in (the HR app's separate Google environment → onto the Hub)
so the platform converges rather than fragments.

**From experience — what works and what to avoid.** Works: start small, ship something real fast,
co-design with users, extract shared infrastructure from real second cases. Avoid: big-bang platform
rewrites, abstracting before you have two concrete users of the abstraction, and "the AI built it"
black boxes that the client can't maintain — the fastest route back to silos and dependence.
