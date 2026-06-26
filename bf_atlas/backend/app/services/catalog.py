"""
catalog.py — Brand Catalog + shareable PDF (spec §7 supporting outputs).

A company-wide list of every brand BF moves, exportable as a clean PDF for new
clients ("here's what we can supply") or suppliers ("here's what we distribute"),
with NO internal data exposed — no prices, clients, suppliers, margins or traders.

PDF generation is pure-Python (reportlab) with a no-dependency text fallback so it
always works in the POC.
"""

import io

from app.services import brands


def catalog_rows():
    df = brands.catalog()
    return [
        {"brand": r["brand"], "category": r["category"],
         "products": int(r["products"]) if r["products"] else 0}
        for _, r in df.iterrows()
    ]


def build_pdf() -> tuple[bytes, str]:
    """Return (bytes, media_type). Anonymised — brands + categories only."""
    rows = catalog_rows()
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        y = h - 2 * cm
        c.setFont("Helvetica-Bold", 18)
        c.drawString(2 * cm, y, "B Futurist — Brand Catalogue")
        y -= 0.8 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, "The brands we distribute. No pricing or account data.")
        y -= 1.0 * cm

        last_cat = None
        for r in sorted(rows, key=lambda x: (x["category"] or "", x["brand"])):
            if r["category"] != last_cat:
                last_cat = r["category"]
                y -= 0.3 * cm
                if y < 2.5 * cm:
                    c.showPage(); y = h - 2 * cm
                c.setFont("Helvetica-Bold", 12)
                c.drawString(2 * cm, y, (last_cat or "Other").title())
                y -= 0.6 * cm
            if y < 2 * cm:
                c.showPage(); y = h - 2 * cm
            c.setFont("Helvetica", 10)
            c.drawString(2.5 * cm, y, f"• {r['brand']}  ({r['products']} products)")
            y -= 0.5 * cm
        c.showPage()
        c.save()
        return buf.getvalue(), "application/pdf"
    except ImportError:
        # Fallback: plain text so the export endpoint never hard-fails in the POC.
        lines = ["B Futurist — Brand Catalogue", ""]
        last_cat = None
        for r in sorted(rows, key=lambda x: (x["category"] or "", x["brand"])):
            if r["category"] != last_cat:
                last_cat = r["category"]
                lines.append(f"\n[{(last_cat or 'Other').title()}]")
            lines.append(f"  - {r['brand']} ({r['products']} products)")
        return ("\n".join(lines)).encode("utf-8"), "text/plain"
