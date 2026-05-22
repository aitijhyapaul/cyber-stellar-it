from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from database import get_db
from models import User, Order, Inquiry, PaymentStatus, InquiryStatus, OrderStatus
from schemas import UserOut, DashboardStats, OrderStatusUpdate
import auth as auth_module

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    total_users = db.query(func.count(User.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()
    total_inquiries = db.query(func.count(Inquiry.id)).scalar()
    total_revenue = db.query(func.sum(Order.amount)).filter(
        Order.payment_status == PaymentStatus.paid
    ).scalar() or 0.0
    pending_orders = db.query(func.count(Order.id)).filter(
        Order.status == OrderStatus.pending
    ).scalar()
    new_inquiries = db.query(func.count(Inquiry.id)).filter(
        Inquiry.status == InquiryStatus.new
    ).scalar()
    awaiting_verification = db.query(func.count(Order.id)).filter(
        Order.payment_status == PaymentStatus.awaiting_verification
    ).scalar()

    return DashboardStats(
        total_users=total_users,
        total_orders=total_orders,
        total_inquiries=total_inquiries,
        total_revenue=total_revenue,
        pending_orders=pending_orders,
        new_inquiries=new_inquiries,
        awaiting_verification=awaiting_verification,
    )


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/toggle-active", response_model=UserOut)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot deactivate admin accounts")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/make-admin", response_model=UserOut)
def make_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return user
