from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class ServiceType(str, enum.Enum):
    fixed = "fixed"
    quote = "quote"
    subscription = "subscription"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class PaymentStatus(str, enum.Enum):
    pending = "pending"           # invoice issued, awaiting transfer
    awaiting_verification = "awaiting_verification"  # customer submitted transfer ref
    paid = "paid"                 # admin verified
    rejected = "rejected"         # admin rejected (wrong amount, fake ref, etc.)
    refunded = "refunded"


class PaymentMethod(str, enum.Enum):
    bank_transfer = "bank_transfer"
    wire_transfer = "wire_transfer"
    other = "other"


class InquiryStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    converted = "converted"
    closed = "closed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")
    inquiries = relationship("Inquiry", back_populates="user")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    short_description = Column(String, nullable=False)
    full_description = Column(Text, nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    price = Column(Float, nullable=True)
    price_label = Column(String, nullable=True)
    features = Column(Text, nullable=False, default="[]")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="service")
    inquiries = relationship("Inquiry", back_populates="service")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    amount = Column(Float, nullable=True)
    currency = Column(String, default="bdt")

    payment_method = Column(Enum(PaymentMethod), nullable=True)
    transfer_reference = Column(String, nullable=True)  # bank txn id / wire ref customer submitted
    transfer_date = Column(DateTime, nullable=True)     # when customer says they sent it
    paid_at = Column(DateTime, nullable=True)           # when admin verified payment
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payment_notes = Column(Text, nullable=True)         # customer's note when submitting (e.g. "sent from XYZ bank")
    rejection_reason = Column(Text, nullable=True)

    customer_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    service = relationship("Service", back_populates="orders")
    verified_by = relationship("User", foreign_keys=[verified_by_id])


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    status = Column(Enum(InquiryStatus), default=InquiryStatus.new)
    created_at = Column(DateTime, default=datetime.utcnow)

    service = relationship("Service", back_populates="inquiries")
    user = relationship("User", back_populates="inquiries")
