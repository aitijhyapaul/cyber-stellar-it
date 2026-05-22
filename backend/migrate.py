"""
One-shot migration: convert orders table from Stripe-based to bank-transfer-based.

Safe to run multiple times — checks for column existence before altering.
SQLite ALTER TABLE is limited but supports ADD COLUMN, which is all we need
since we're keeping (but no longer writing to) stripe_payment_intent_id.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import inspect, text
from database import engine, SessionLocal
from models import Base


NEW_ORDER_COLUMNS = [
    ("payment_method", "VARCHAR"),
    ("transfer_reference", "VARCHAR"),
    ("transfer_date", "DATETIME"),
    ("paid_at", "DATETIME"),
    ("verified_by_id", "INTEGER"),
    ("payment_notes", "TEXT"),
    ("rejection_reason", "TEXT"),
]


def migrate():
    # First make sure all tables exist (covers fresh DB case).
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    existing_cols = {col["name"] for col in inspector.get_columns("orders")}

    with engine.begin() as conn:
        for col_name, col_type in NEW_ORDER_COLUMNS:
            if col_name in existing_cols:
                print(f"  ~ orders.{col_name} already exists")
                continue
            conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}"))
            print(f"  + Added orders.{col_name}")

        # Default currency to bdt for new orders going forward — existing rows keep their value.
        # Also update any 'failed' payment_status rows to 'rejected' for label consistency (optional).
        # No-op if nothing matches.
        conn.execute(text("UPDATE orders SET currency = 'bdt' WHERE currency IS NULL OR currency = ''"))

    print("Migration complete.")


if __name__ == "__main__":
    migrate()
