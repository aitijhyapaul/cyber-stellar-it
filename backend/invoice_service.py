"""
Generate PDF invoices for orders.

Pulls company + bank details from environment (placeholders until user fills in).
Renders BDT primary with USD shown alongside (using USD_TO_BDT_RATE).
"""
import os
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)


COMPANY = {
    "name": os.getenv("SITE_NAME", "Cyber Stellar IT"),
    "address": os.getenv("COMPANY_ADDRESS", "TODO: Company Address, Dhaka, Bangladesh"),
    "email": os.getenv("ADMIN_EMAIL", "contact@example.com"),
    "phone": os.getenv("COMPANY_PHONE", "TODO: +880 ..."),
    "website": os.getenv("COMPANY_WEBSITE", "cyberstellarbd.com"),
}

ACCENT = colors.HexColor("#06b6d4")  # cyan
MUTED = colors.HexColor("#6b7280")
DARK = colors.HexColor("#111827")


def _rate() -> float:
    try:
        return float(os.getenv("USD_TO_BDT_RATE", "120.0"))
    except ValueError:
        return 120.0


def invoice_number(order) -> str:
    return f"INV-{order.created_at.strftime('%Y%m')}-{order.id:05d}"


def _bank_blocks():
    local = {
        "Bank": os.getenv("BANK_NAME", "TODO: Your Bank Name"),
        "Account Name": os.getenv("BANK_ACCOUNT_NAME", "TODO: Account Holder"),
        "Account Number": os.getenv("BANK_ACCOUNT_NUMBER", "TODO: 0000-0000-0000"),
        "Branch": os.getenv("BANK_BRANCH", "TODO: Branch"),
        "Routing": os.getenv("BANK_ROUTING", "TODO: Routing #"),
    }
    intl = {
        "Bank": os.getenv("WIRE_BANK_NAME", "TODO: International Bank"),
        "Account Name": os.getenv("WIRE_ACCOUNT_NAME", "TODO: Account Holder"),
        "Account / IBAN": os.getenv("WIRE_ACCOUNT_NUMBER", "TODO: IBAN"),
        "SWIFT / BIC": os.getenv("WIRE_SWIFT", "TODO: SWIFT"),
        "Bank Address": os.getenv("WIRE_BANK_ADDRESS", "TODO: Bank Address"),
    }
    return local, intl


def generate_invoice_pdf(order) -> bytes:
    """Returns the PDF bytes for an order's invoice."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Invoice {invoice_number(order)}",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=DARK, fontSize=22, leading=26)
    h_label = ParagraphStyle("hlabel", parent=styles["Normal"], textColor=MUTED, fontSize=8, leading=10, spaceAfter=2)
    h_value = ParagraphStyle("hvalue", parent=styles["Normal"], textColor=DARK, fontSize=10, leading=13)
    body = ParagraphStyle("body", parent=styles["Normal"], textColor=DARK, fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=styles["Normal"], textColor=MUTED, fontSize=8, leading=11)
    section = ParagraphStyle("section", parent=styles["Heading3"], textColor=ACCENT, fontSize=11, leading=14, spaceBefore=6, spaceAfter=4)

    story = []

    # Header
    header_data = [[
        Paragraph(f"<b>{COMPANY['name']}</b>", h1),
        Paragraph(
            f"<b>INVOICE</b><br/>"
            f"<font color='#6b7280'>#{invoice_number(order)}</font>",
            ParagraphStyle("inv", parent=styles["Normal"], fontSize=12, leading=16, alignment=2, textColor=DARK),
        ),
    ]]
    header_tbl = Table(header_data, colWidths=[None, 70 * mm])
    header_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(header_tbl)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=2))
    story.append(Spacer(1, 8))

    # From / To
    customer_name = order.user.full_name if order.user else "Customer"
    customer_email = order.user.email if order.user else ""
    addr_data = [[
        [
            Paragraph("FROM", h_label),
            Paragraph(f"<b>{COMPANY['name']}</b>", h_value),
            Paragraph(COMPANY["address"], small),
            Paragraph(f"{COMPANY['email']} · {COMPANY['phone']}", small),
            Paragraph(COMPANY["website"], small),
        ],
        [
            Paragraph("BILL TO", h_label),
            Paragraph(f"<b>{customer_name}</b>", h_value),
            Paragraph(customer_email, small),
        ],
        [
            Paragraph("ISSUE DATE", h_label),
            Paragraph(datetime.utcnow().strftime("%d %b %Y"), h_value),
            Spacer(1, 8),
            Paragraph("ORDER #", h_label),
            Paragraph(f"#{order.id}", h_value),
        ],
    ]]
    addr_tbl = Table(addr_data, colWidths=[65 * mm, 55 * mm, 50 * mm])
    addr_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(addr_tbl)
    story.append(Spacer(1, 14))

    # Line items
    service_name = order.service.name if order.service else "Service"
    amount_bdt = order.amount or 0.0
    currency = (order.currency or "bdt").lower()
    rate = _rate()
    if currency == "usd":
        amount_usd = amount_bdt
        amount_bdt_display = amount_bdt * rate
    else:
        amount_usd = amount_bdt / rate if rate else 0
        amount_bdt_display = amount_bdt

    items_data = [
        ["Description", "Qty", "Amount (BDT)", "Amount (USD)"],
        [
            Paragraph(f"<b>{service_name}</b><br/><font color='#6b7280' size='8'>{(order.customer_notes or '')[:120]}</font>", body),
            "1",
            f"Tk {amount_bdt_display:,.2f}",
            f"$ {amount_usd:,.2f}",
        ],
    ]
    items_tbl = Table(items_data, colWidths=[None, 18 * mm, 38 * mm, 35 * mm])
    items_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    story.append(items_tbl)
    story.append(Spacer(1, 8))

    # Totals
    totals_data = [
        ["", "Subtotal (BDT)", f"Tk {amount_bdt_display:,.2f}"],
        ["", "Subtotal (USD ≈)", f"$ {amount_usd:,.2f}"],
        ["", "TOTAL DUE", f"Tk {amount_bdt_display:,.2f}"],
    ]
    totals_tbl = Table(totals_data, colWidths=[None, 50 * mm, 40 * mm])
    totals_tbl.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (1, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (1, 2), (-1, 2), 12),
        ("TEXTCOLOR", (1, 2), (-1, 2), ACCENT),
        ("LINEABOVE", (1, 2), (-1, 2), 1, ACCENT),
        ("TOPPADDING", (1, 2), (-1, 2), 8),
    ]))
    story.append(totals_tbl)
    story.append(Spacer(1, 14))
    story.append(Paragraph(f"<i>USD shown at indicative rate 1 USD ≈ {rate:.2f} BDT. Final amount payable is in BDT unless otherwise agreed.</i>", small))
    story.append(Spacer(1, 16))

    # Payment instructions
    local, intl = _bank_blocks()
    story.append(Paragraph("Payment Instructions", section))
    story.append(Paragraph(
        f"Please reference <b>Order #{order.id}</b> / <b>{invoice_number(order)}</b> in your transfer memo. "
        f"After sending, submit your transfer reference at <b>{COMPANY['website']}/checkout.html?order={order.id}</b>.",
        body,
    ))
    story.append(Spacer(1, 8))

    bank_data = [
        [Paragraph("<b>Local Bank Transfer (BDT)</b>", h_value), Paragraph("<b>International Wire Transfer (USD)</b>", h_value)],
        [
            "\n".join(f"{k}:  {v}" for k, v in local.items()),
            "\n".join(f"{k}:  {v}" for k, v in intl.items()),
        ],
    ]
    bank_tbl = Table(bank_data, colWidths=["50%", "50%"])
    bank_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(bank_tbl)

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#e5e7eb"), thickness=0.5))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Thank you for your business. Questions? Contact us at {COMPANY['email']}.",
        small,
    ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf
