"""Run once to seed the database with initial services and admin user."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
from models import Base, Service, User, ServiceType
from auth import hash_password

Base.metadata.create_all(bind=engine)

SERVICES = [
    {
        "name": "Website Development",
        "slug": "website-development",
        "short_description": "Custom HTML/CSS websites and redesigns built to perform.",
        "full_description": (
            "We build clean, fast, and fully responsive websites from scratch using HTML, CSS, and JavaScript. "
            "Whether you need a brand new site or want to modernize an existing one, we handle everything — "
            "from design to deployment. Every site is optimized for speed, SEO, and mobile."
        ),
        "service_type": ServiceType.quote,
        "price": None,
        "price_label": "Custom Quote",
        "features": json.dumps([
            "Custom design from scratch",
            "Fully responsive (mobile, tablet, desktop)",
            "SEO-optimized structure",
            "Fast loading & performance tuned",
            "2 rounds of revisions included",
            "Ongoing maintenance available",
        ]),
    },
    {
        "name": "SaaS ERP Software",
        "slug": "erp-software",
        "short_description": "Production-ready ERP system deployed for your business.",
        "full_description": (
            "Get a full-featured ERP system tailored to your manufacturing or service business. "
            "Built on modern technology, our ERP covers inventory, procurement, sales, HR, and reporting. "
            "One-time deployment fee to get you live, with a yearly renewal for support and updates."
        ),
        "service_type": ServiceType.subscription,
        "price": None,
        "price_label": "One-time deployment + Yearly renewal",
        "features": json.dumps([
            "Inventory & procurement management",
            "Sales & customer tracking",
            "HR & payroll module",
            "Financial reporting & dashboards",
            "Multi-user with role-based access",
            "Cloud-hosted, accessible anywhere",
            "Full onboarding & training session",
            "Priority support on yearly plan",
        ]),
    },
    {
        "name": "Digital Marketing",
        "slug": "digital-marketing",
        "short_description": "SEO, social media management, and paid ad campaigns.",
        "full_description": (
            "We grow your online presence through targeted digital marketing strategies. "
            "From ranking higher on Google with SEO, to managing your social media channels, "
            "to running high-converting paid ad campaigns on Google and Facebook — we handle it all."
        ),
        "service_type": ServiceType.quote,
        "price": None,
        "price_label": "Custom Quote",
        "features": json.dumps([
            "Search Engine Optimization (SEO)",
            "Social media management (Instagram, Facebook, LinkedIn)",
            "Google & Facebook paid ad campaigns",
            "Monthly performance reports",
            "Competitor analysis",
            "Content strategy & copywriting",
        ]),
    },
    {
        "name": "Lead Generation",
        "slug": "lead-generation",
        "short_description": "Qualified, targeted contact lists delivered to you.",
        "full_description": (
            "Stop wasting time hunting for prospects. We research and compile highly targeted lists of "
            "qualified leads in your industry, complete with contact details. "
            "You get a clean spreadsheet of decision-makers ready to reach out to."
        ),
        "service_type": ServiceType.fixed,
        "price": 10.0,
        "price_label": "$10 per lead",
        "features": json.dumps([
            "Industry & niche-specific targeting",
            "Verified email addresses",
            "LinkedIn profiles included where available",
            "Phone numbers where available",
            "Company name, size & location data",
            "Delivered as clean spreadsheet (CSV/Excel)",
            "Turnaround within 3-5 business days",
        ]),
    },
]

ADMIN = {
    "email": os.getenv("ADMIN_EMAIL", "admin@example.com"),
    "full_name": "Admin",
    "password": os.getenv("ADMIN_PASSWORD", "changeme123"),
    "is_admin": True,
}


def seed():
    db = SessionLocal()
    try:
        for svc_data in SERVICES:
            exists = db.query(Service).filter(Service.slug == svc_data["slug"]).first()
            if not exists:
                db.add(Service(**svc_data))
                print(f"  + Service: {svc_data['name']}")
            else:
                print(f"  ~ Service already exists: {svc_data['name']}")

        admin = db.query(User).filter(User.email == ADMIN["email"]).first()
        if not admin:
            db.add(User(
                email=ADMIN["email"],
                full_name=ADMIN["full_name"],
                hashed_password=hash_password(ADMIN["password"]),
                is_admin=True,
            ))
            print(f"  + Admin user: {ADMIN['email']}")
        else:
            print(f"  ~ Admin already exists: {ADMIN['email']}")

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
