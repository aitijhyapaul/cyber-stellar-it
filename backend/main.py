from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine
from models import Base
from routes.auth_routes import router as auth_router
from routes.services_routes import router as services_router
from routes.orders_routes import router as orders_router
from routes.payments_routes import router as payments_router
from routes.inquiries_routes import router as inquiries_router
from routes.admin_routes import router as admin_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Services API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc")

FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(services_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(inquiries_router)
app.include_router(admin_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
