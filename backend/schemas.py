from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import ServiceType, OrderStatus, PaymentStatus, PaymentMethod, InquiryStatus


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ── Services ──────────────────────────────────────────────────────────────────

class ServiceOut(BaseModel):
    id: int
    name: str
    slug: str
    short_description: str
    full_description: str
    service_type: ServiceType
    price: Optional[float]
    price_label: Optional[str]
    features: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceCreate(BaseModel):
    name: str
    slug: str
    short_description: str
    full_description: str
    service_type: ServiceType
    price: Optional[float] = None
    price_label: Optional[str] = None
    features: str = "[]"


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    service_type: Optional[ServiceType] = None
    price: Optional[float] = None
    price_label: Optional[str] = None
    features: Optional[str] = None
    is_active: Optional[bool] = None


# ── Orders ────────────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    service_id: int
    customer_notes: Optional[str] = None


class OrderOut(BaseModel):
    id: int
    user_id: int
    service_id: int
    status: OrderStatus
    payment_status: PaymentStatus
    amount: Optional[float]
    currency: str
    payment_method: Optional[PaymentMethod]
    transfer_reference: Optional[str]
    transfer_date: Optional[datetime]
    paid_at: Optional[datetime]
    payment_notes: Optional[str]
    rejection_reason: Optional[str]
    customer_notes: Optional[str]
    admin_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    service: ServiceOut
    user: UserOut

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    admin_notes: Optional[str] = None
    amount: Optional[float] = None  # admin sets price after quoting (for `quote` services)


# ── Payments (bank/wire transfer) ────────────────────────────────────────────

class BankDetailsOut(BaseModel):
    """Public bank details shown to customer at checkout."""
    local: dict   # BDT bank transfer
    international: dict  # USD wire transfer (SWIFT)
    company_name: str
    notes: Optional[str] = None


class PaymentSubmit(BaseModel):
    """Customer submits proof they made a bank/wire transfer."""
    order_id: int
    payment_method: PaymentMethod
    transfer_reference: str  # bank txn ID / wire ref
    transfer_date: Optional[datetime] = None
    notes: Optional[str] = None


class PaymentVerify(BaseModel):
    """Admin verifies or rejects a submitted payment."""
    approve: bool
    rejection_reason: Optional[str] = None


class InvoicePreview(BaseModel):
    order_id: int
    invoice_number: str
    issue_date: datetime
    amount_bdt: float
    amount_usd: Optional[float] = None
    exchange_rate: Optional[float] = None
    customer_name: str
    customer_email: str
    service_name: str


# ── Inquiries ─────────────────────────────────────────────────────────────────

class InquiryCreate(BaseModel):
    service_id: Optional[int] = None
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str


class InquiryOut(BaseModel):
    id: int
    service_id: Optional[int]
    user_id: Optional[int]
    name: str
    email: str
    phone: Optional[str]
    message: str
    status: InquiryStatus
    created_at: datetime

    class Config:
        from_attributes = True


class InquiryStatusUpdate(BaseModel):
    status: InquiryStatus


# ── Admin ─────────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_users: int
    total_orders: int
    total_inquiries: int
    total_revenue: float
    pending_orders: int
    new_inquiries: int
    awaiting_verification: int
