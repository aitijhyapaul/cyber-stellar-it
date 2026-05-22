"""
Bank / wire transfer payment flow.

Flow:
  1. Customer places order   → status=pending, payment_status=pending
  2. /api/payments/bank-details   →  customer sees how to pay
  3. /api/payments/submit         →  customer submits transfer reference
                                      → payment_status=awaiting_verification
  4. Admin verifies in dashboard  → /api/payments/{order_id}/verify
                                      → payment_status=paid  (or rejected)
"""
import os
import secrets
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from models import Order, User, Service, PaymentStatus, PaymentMethod
from schemas import PaymentSubmit, PaymentVerify, BankDetailsOut, OrderOut
import auth as auth_module
import email_service
import invoice_service


router = APIRouter(prefix="/api/payments", tags=["payments"])


def _bank_details() -> dict:
    """Pulls bank info from environment. Placeholders until user fills .env."""
    return {
        "local": {
            "bank_name": os.getenv("BANK_NAME", "TODO: Your Bank Name"),
            "account_name": os.getenv("BANK_ACCOUNT_NAME", "TODO: Account Holder Name"),
            "account_number": os.getenv("BANK_ACCOUNT_NUMBER", "TODO: 0000-0000-0000"),
            "branch": os.getenv("BANK_BRANCH", "TODO: Branch Name"),
            "routing_number": os.getenv("BANK_ROUTING", "TODO: Routing Number"),
            "currency": "BDT",
        },
        "international": {
            "bank_name": os.getenv("WIRE_BANK_NAME", "TODO: International Bank Name"),
            "account_name": os.getenv("WIRE_ACCOUNT_NAME", "TODO: Account Holder Name"),
            "account_number": os.getenv("WIRE_ACCOUNT_NUMBER", "TODO: IBAN / Account Number"),
            "swift_code": os.getenv("WIRE_SWIFT", "TODO: SWIFT/BIC"),
            "bank_address": os.getenv("WIRE_BANK_ADDRESS", "TODO: Bank Address"),
            "currency": "USD",
        },
        "company_name": os.getenv("SITE_NAME", "Cyber Stellar IT"),
        "notes": (
            "Please include your Order ID in the transfer reference/memo. "
            "After sending, submit the transfer reference on the checkout page so we can verify."
        ),
    }


def _exchange_rate() -> float:
    """USD → BDT rate. Read from env so admin can keep it current."""
    try:
        return float(os.getenv("USD_TO_BDT_RATE", "120.0"))
    except ValueError:
        return 120.0


@router.get("/bank-details", response_model=BankDetailsOut)
def bank_details():
    return _bank_details()


@router.get("/exchange-rate")
def exchange_rate():
    rate = _exchange_rate()
    return {"usd_to_bdt": rate, "bdt_to_usd": round(1.0 / rate, 6) if rate else None}


@router.get("/{order_id}/invoice")
def download_invoice(
    order_id: int,
    token: Optional[str] = None,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Download a PDF invoice for an order.

    Auth: standard Bearer header OR ?token=... query param (so plain <a> links work).
    """
    raw_token = token
    if not raw_token and authorization and authorization.lower().startswith("bearer "):
        raw_token = authorization.split(" ", 1)[1]
    user = auth_module.get_user_from_token(raw_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    if not order.amount or order.amount <= 0:
        raise HTTPException(status_code=400, detail="No invoice — order has no amount yet")

    pdf = invoice_service.generate_invoice_pdf(order)
    filename = f"{invoice_service.invoice_number(order)}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/submit", response_model=OrderOut)
def submit_payment(
    data: PaymentSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_module.get_current_user),
):
    """Customer submits proof of bank/wire transfer."""
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not order.amount or order.amount <= 0:
        raise HTTPException(status_code=400, detail="This order has no amount yet — awaiting quote from admin")
    if order.payment_status == PaymentStatus.paid:
        raise HTTPException(status_code=400, detail="Order already paid")

    if not data.transfer_reference or not data.transfer_reference.strip():
        raise HTTPException(status_code=400, detail="Transfer reference is required")

    order.payment_method = data.payment_method
    order.transfer_reference = data.transfer_reference.strip()
    order.transfer_date = data.transfer_date or datetime.utcnow()
    order.payment_notes = data.notes
    order.payment_status = PaymentStatus.awaiting_verification
    order.rejection_reason = None
    db.commit()
    db.refresh(order)

    email_service.send_payment_submitted_admin_alert(
        order.user.full_name, order.user.email, order.id,
        order.service.name, order.amount, order.currency,
        order.transfer_reference, data.payment_method.value
    )
    email_service.send_payment_received_customer(
        order.user.email, order.user.full_name, order.id, order.transfer_reference
    )

    return order


@router.post("/{order_id}/verify", response_model=OrderOut)
def verify_payment(
    order_id: int,
    data: PaymentVerify,
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    """Admin approves or rejects a submitted bank/wire transfer."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.payment_status not in (PaymentStatus.awaiting_verification, PaymentStatus.rejected):
        raise HTTPException(
            status_code=400,
            detail=f"Order is in '{order.payment_status.value}' state — only awaiting_verification can be verified",
        )

    if data.approve:
        order.payment_status = PaymentStatus.paid
        order.paid_at = datetime.utcnow()
        order.verified_by_id = admin.id
        order.rejection_reason = None
        db.commit()
        db.refresh(order)
        email_service.send_payment_verified_customer(
            order.user.email, order.user.full_name, order.service.name, order.amount, order.currency, order.id
        )
    else:
        if not data.rejection_reason or not data.rejection_reason.strip():
            raise HTTPException(status_code=400, detail="Rejection reason is required when rejecting payment")
        order.payment_status = PaymentStatus.rejected
        order.rejection_reason = data.rejection_reason.strip()
        order.verified_by_id = admin.id
        db.commit()
        db.refresh(order)
        email_service.send_payment_rejected_customer(
            order.user.email, order.user.full_name, order.id, data.rejection_reason.strip()
        )

    return order


# ── Guest checkout — optional, creates user + order in one shot ──────────────

class GuestCheckoutRequest(BaseModel):
    service_slug: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    quantity: int = 1
    notes: Optional[str] = None


class GuestCheckoutResponse(BaseModel):
    order_id: int
    amount: float
    currency: str
    bank_details: dict
    invoice_url: str


@router.post("/guest-checkout", response_model=GuestCheckoutResponse)
def guest_checkout(data: GuestCheckoutRequest, db: Session = Depends(get_db)):
    """Create a guest order and return bank transfer instructions (no Stripe, no payment yet)."""
    service = db.query(Service).filter(Service.slug == data.service_slug, Service.is_active == True).first()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{data.service_slug}' not found")

    if not service.price or service.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="This service has no fixed price — please use the inquiry form for a custom quote",
        )

    if data.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")

    amount = service.price * data.quantity

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        random_password = secrets.token_urlsafe(24)
        user = User(
            email=data.email,
            full_name=data.name,
            hashed_password=auth_module.hash_password(random_password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    notes_combined = f"Quantity: {data.quantity}"
    if data.phone:
        notes_combined += f"\nPhone: {data.phone}"
    if data.notes:
        notes_combined += f"\nNotes: {data.notes}"

    order = Order(
        user_id=user.id,
        service_id=service.id,
        amount=amount,
        currency="bdt",
        customer_notes=notes_combined,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    email_service.send_order_admin_alert(service.name, data.name, data.email, order.id, notes_combined)
    email_service.send_order_confirmation(data.email, data.name, service.name, order.id)

    return {
        "order_id": order.id,
        "amount": amount,
        "currency": order.currency,
        "bank_details": _bank_details(),
        "invoice_url": f"/api/payments/{order.id}/invoice",
    }
