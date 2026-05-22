from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Order, Service, User, OrderStatus, ServiceType
from schemas import OrderCreate, OrderOut, OrderStatusUpdate
import auth as auth_module
import email_service

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_module.get_current_user),
):
    service = db.query(Service).filter(Service.id == data.service_id, Service.is_active == True).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    order = Order(
        user_id=current_user.id,
        service_id=service.id,
        amount=service.price,
        currency="bdt",
        customer_notes=data.customer_notes,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    email_service.send_order_confirmation(current_user.email, current_user.full_name, service.name, order.id)
    email_service.send_order_admin_alert(service.name, current_user.full_name, current_user.email, order.id, data.customer_notes or "")

    return order


@router.get("/my", response_model=List[OrderOut])
def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_module.get_current_user),
):
    return db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_module.get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return order


@router.patch("/{order_id}", response_model=OrderOut)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if data.status:
        order.status = data.status
    if data.admin_notes is not None:
        order.admin_notes = data.admin_notes
    if data.amount is not None:
        if data.amount < 0:
            raise HTTPException(status_code=400, detail="Amount cannot be negative")
        order.amount = data.amount
    db.commit()
    db.refresh(order)
    return order


@router.get("/admin/all", response_model=List[OrderOut])
def all_orders(
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    return db.query(Order).order_by(Order.created_at.desc()).all()
