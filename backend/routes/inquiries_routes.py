from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Inquiry, Service, User
from schemas import InquiryCreate, InquiryOut, InquiryStatusUpdate
import auth as auth_module
import email_service

router = APIRouter(prefix="/api/inquiries", tags=["inquiries"])


@router.post("/", response_model=InquiryOut, status_code=201)
def create_inquiry(data: InquiryCreate, db: Session = Depends(get_db)):
    service = None
    if data.service_id:
        service = db.query(Service).filter(Service.id == data.service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")

    inquiry = Inquiry(
        service_id=data.service_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        message=data.message,
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    email_service.send_inquiry_confirmation(data.email, data.name, service.name if service else "")
    email_service.send_inquiry_admin_alert(data.name, data.email, data.message, service.name if service else "")

    return inquiry


@router.get("/admin/all", response_model=List[InquiryOut])
def all_inquiries(
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    return db.query(Inquiry).order_by(Inquiry.created_at.desc()).all()


@router.patch("/admin/{inquiry_id}", response_model=InquiryOut)
def update_inquiry_status(
    inquiry_id: int,
    data: InquiryStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(auth_module.get_current_admin),
):
    inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    inquiry.status = data.status
    db.commit()
    db.refresh(inquiry)
    return inquiry
