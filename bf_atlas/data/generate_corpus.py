"""
generate_corpus.py — synthetic UNSTRUCTURED corpus for the RAG layer.

Atlas's structured data lives in SQLite (orders, deals, …). RAG needs free text —
the kind of content Odoo/NetHunt actually hold beyond columns: deal notes,
supplier emails, brand briefs, trader call summaries. This generates that corpus,
region-tagged so the same region RBAC applies to retrieval.

Output:  data/corpus.json   Run:  python generate_corpus.py
"""

import json
import os
import random

random.seed(11)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "corpus.json")

REGIONS = ["EU-West", "Asia-Pacific", "Americas", "Middle-East", "Southeast-Asia"]
BRANDS = ["Maison Luxe", "Floral Studio", "Arabian Essence", "Blue Ocean Co",
          "Artisan Blend", "Glow Lab", "HydraLux", "Colour Story", "Silk & Shine"]
SUPPLIERS = ["Étoile Distribution", "Gulf Scent Trading", "Pearl River Beauty",
             "Nordic Skin Labs", "Tokyo Glow Import", "Iberia Fragrance House"]
COMPANIES = ["Munoz-Gray", "Medina Inc", "Ramirez-Hall", "Aurora Beauty Group",
             "Crescent Retail Co", "Pearl Trading", "Summit Cosmetics", "Harbor Brands",
             "Zenith Imports", "Cobalt Stores", "Verdant Partners", "Ember Holdings"]

# Specific, retrievable facts (so demo queries return something concrete).
SEEDED = [
    {"type": "deal_note", "region": "Southeast-Asia",
     "title": "Munoz-Gray — pricing concern on Oud Royale",
     "text": "Call with Munoz-Gray procurement. They love Arabian Essence Oud Royale but "
             "pushed back hard on our €180 list price — competitor quoted them €165. "
             "They'll commit to 200 units if we hold €170. Risk of losing the account if we don't move."},
    {"type": "supplier_email", "region": "Middle-East",
     "title": "Gulf Scent Trading — shipping delay on Velvet Oud",
     "text": "From: ops@gulfscent.ae. Heads up: a 3-week shipping delay on Velvet Oud due to "
             "customs at Jebel Ali. New ETA mid-next-month. We can offer Amber Nights as a "
             "substitute at the same wholesale price if your clients need stock sooner."},
    {"type": "supplier_email", "region": "EU-West",
     "title": "Étoile Distribution — Maison Luxe price drop",
     "text": "From: sales@etoile.fr. Good news — we're dropping Maison Luxe Lumière Dorée by "
             "8% for Q3 orders above 300 units. This is a clearance ahead of new packaging; "
             "limited window, valid two weeks."},
    {"type": "deal_note", "region": "EU-West",
     "title": "Aurora Beauty Group — stalled, no response",
     "text": "Aurora Beauty Group went quiet after the proposal for Glow Lab skincare. Last "
             "contact was 3 weeks ago. They mentioned budget freeze until next quarter. "
             "Recommend a check-in and a smaller trial order to keep it warm."},
    {"type": "brand_doc", "region": None,
     "title": "Arabian Essence — brand profile",
     "text": "Arabian Essence is our premium oud house: deep, woody, smoky oriental fragrances "
             "(Oud Royale, Velvet Oud). High margin, strong demand in Middle-East and "
             "Southeast-Asia. Positioned against niche luxury perfumers; best paired with "
             "gift-set bundles for retail."},
    {"type": "brand_doc", "region": None,
     "title": "Glow Lab — brand profile",
     "text": "Glow Lab is a results-driven skincare line — Vitamin C serum, retinol night cream. "
             "Mid-price, fast-moving, popular with younger retail buyers. Margins are thinner "
             "than fragrance but volume is high. Good entry product for new accounts."},
]

NOTE_TEMPLATES = [
    "Met with {company} about {brand}. Interest is {sentiment}; they asked about {topic}. "
    "Next step: {next_step}.",
    "{company} reviewed our {brand} proposal. {sentiment_sentence} Decision expected within "
    "{weeks} weeks. Watch for {risk}.",
    "Follow-up with {company} on {brand}. {sentiment_sentence} They want {topic} before committing.",
]
EMAIL_TEMPLATES = [
    "From: sales@{supplier_slug}. We can offer {brand} at improved terms this month — {offer}. "
    "Let us know volumes and we'll confirm lead times.",
    "From: ops@{supplier_slug}. Update on {brand}: {logistics}. {substitute}",
    "From: accounts@{supplier_slug}. Reminder on the {brand} order — {logistics}. Please confirm.",
]
BRIEF_TEMPLATES = [
    "{region} weekly briefing: pipeline is {health}. Strongest demand in {brand}. "
    "Key risk: {risk}. Focus this week on {focus}.",
]

SENTIMENTS = ["strong", "lukewarm", "cooling", "very positive", "hesitant"]
SENT_SENTENCES = ["They were enthusiastic about the margins.", "Concerns remain about price.",
                  "Tone was positive but non-committal.", "They compared us to a cheaper competitor.",
                  "Strong fit with their existing range."]
TOPICS = ["bulk pricing", "exclusivity", "minimum order quantity", "payment terms",
          "sample units", "co-marketing support"]
NEXT_STEPS = ["send a revised quote", "arrange a sample shipment", "schedule a follow-up call",
              "draft a trial order", "loop in the regional manager"]
RISKS = ["a competitor undercutting us", "their budget freeze", "a stock shortage",
         "slow internal approval", "FX moving against the deal"]
OFFERS = ["a 6% discount on 250+ units", "free freight on the first order",
          "extended 60-day payment terms", "a bundled gift-set deal"]
LOGISTICS = ["a short delay at port, ETA pushed by one week", "stock is back to normal levels",
             "a partial shipment goes out Friday, remainder next week",
             "we've cleared the backlog and can ship immediately"]
SUBSTITUTES = ["We can substitute a similar SKU if needed.", "No substitute available this cycle.",
               "Happy to hold your allocation for 10 days."]
HEALTHS = ["healthy and growing", "flat versus last month", "soft, needs attention",
           "ahead of target"]
FOCUSES = ["reviving stalled deals", "closing two late-stage proposals",
           "restocking low-inventory brands", "onboarding two new retail accounts"]


def _slug(supplier: str) -> str:
    return supplier.lower().split()[0].replace("é", "e") + ".com"


def generate():
    docs = []
    nid = 1000
    for d in SEEDED:  # give the hand-written seeds stable ids
        docs.append({"id": f"doc-{nid}", **d})
        nid += 1

    for region in REGIONS:
        # deal notes
        for _ in range(8):
            company, brand = random.choice(COMPANIES), random.choice(BRANDS)
            t = random.choice(NOTE_TEMPLATES)
            text = t.format(
                company=company, brand=brand, sentiment=random.choice(SENTIMENTS),
                sentiment_sentence=random.choice(SENT_SENTENCES), topic=random.choice(TOPICS),
                next_step=random.choice(NEXT_STEPS), weeks=random.randint(1, 6),
                risk=random.choice(RISKS),
            )
            docs.append({"id": f"doc-{nid}", "type": "deal_note", "region": region,
                         "title": f"{company} — {brand} note", "text": text})
            nid += 1
        # supplier emails
        for _ in range(5):
            supplier, brand = random.choice(SUPPLIERS), random.choice(BRANDS)
            t = random.choice(EMAIL_TEMPLATES)
            text = t.format(
                supplier_slug=_slug(supplier), brand=brand, offer=random.choice(OFFERS),
                logistics=random.choice(LOGISTICS), substitute=random.choice(SUBSTITUTES),
            )
            docs.append({"id": f"doc-{nid}", "type": "supplier_email", "region": region,
                         "title": f"{supplier} — {brand}", "text": text})
            nid += 1
        # weekly briefing
        docs.append({"id": f"doc-{nid}", "type": "trader_briefing", "region": region,
                     "title": f"{region} weekly briefing",
                     "text": BRIEF_TEMPLATES[0].format(
                         region=region, health=random.choice(HEALTHS), brand=random.choice(BRANDS),
                         risk=random.choice(RISKS), focus=random.choice(FOCUSES))})
        nid += 1

    return docs


def main() -> None:
    random.seed(11)  # re-seed here so import order can't shift it
    docs = generate()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)
    from collections import Counter
    print(f"=== corpus generated: {len(docs)} documents ===")
    print("  by type:  ", dict(Counter(d["type"] for d in docs)))
    print("  by region:", dict(Counter(d["region"] for d in docs)))
    print(f"Saved to: {OUT}")


if __name__ == "__main__":
    main()
