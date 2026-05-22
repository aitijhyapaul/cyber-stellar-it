"""End-to-end smoke test that hammers every endpoint.

Run AFTER seeding and starting the server:
    python seed.py
    uvicorn main:app --port 8100
    python test_e2e.py
"""
import sys
import httpx

BASE = "http://127.0.0.1:8100"

PASS = "[PASS]"
FAIL = "[FAIL]"

results = []


def check(label, condition, detail=""):
    tag = PASS if condition else FAIL
    msg = f"{tag} {label}" + (f"  -- {detail}" if detail and not condition else "")
    print(msg)
    results.append(condition)


def main():
    c = httpx.Client(base_url=BASE, timeout=10.0)

    # ── Health ────────────────────────────────────────────────────────────────
    r = c.get("/api/health")
    check("GET /api/health", r.status_code == 200 and r.json() == {"status": "ok"})

    # ── Public services ───────────────────────────────────────────────────────
    r = c.get("/api/services/")
    check("GET /api/services/ (list)", r.status_code == 200 and len(r.json()) == 4,
          f"status={r.status_code} body={r.text[:200]}")
    services = r.json()
    slugs = {s["slug"] for s in services}
    check("All 4 service slugs present", slugs == {
        "website-development", "erp-software", "digital-marketing", "lead-generation"
    }, f"got {slugs}")

    r = c.get("/api/services/lead-generation")
    check("GET /api/services/{slug}", r.status_code == 200 and r.json()["slug"] == "lead-generation")

    r = c.get("/api/services/does-not-exist")
    check("GET /api/services/{bad-slug} returns 404", r.status_code == 404)

    # ── Register + login ──────────────────────────────────────────────────────
    import random
    suffix = random.randint(10000, 99999)
    user_email = f"customer{suffix}@example.com"
    user_pass = "StrongPass123!"

    r = c.post("/api/auth/register", json={
        "email": user_email,
        "full_name": "Test Customer",
        "password": user_pass,
    })
    check("POST /api/auth/register", r.status_code == 201,
          f"status={r.status_code} body={r.text[:200]}")
    body = r.json()
    check("Register returns token + user", "access_token" in body and body["user"]["email"] == user_email)
    user_token = body["access_token"]

    r = c.post("/api/auth/register", json={
        "email": user_email, "full_name": "Dup", "password": "xxxx"
    })
    check("Register duplicate email returns 400", r.status_code == 400)

    r = c.post("/api/auth/login", json={"email": user_email, "password": "wrong"})
    check("Login with wrong password returns 401", r.status_code == 401)

    r = c.post("/api/auth/login", json={"email": user_email, "password": user_pass})
    check("POST /api/auth/login", r.status_code == 200 and "access_token" in r.json())
    user_token = r.json()["access_token"]

    auth_h = {"Authorization": f"Bearer {user_token}"}

    r = c.get("/api/auth/me", headers=auth_h)
    check("GET /api/auth/me", r.status_code == 200 and r.json()["email"] == user_email)

    r = c.get("/api/auth/me")
    check("GET /api/auth/me without token returns 401", r.status_code == 401)

    r = c.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    check("GET /api/auth/me with bad token returns 401", r.status_code == 401)

    # ── Admin login ───────────────────────────────────────────────────────────
    r = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "changeme123"})
    check("Admin login", r.status_code == 200, f"status={r.status_code} body={r.text[:200]}")
    admin_token = r.json()["access_token"]
    admin_h = {"Authorization": f"Bearer {admin_token}"}

    # ── Inquiries ─────────────────────────────────────────────────────────────
    service_id = next(s["id"] for s in services if s["slug"] == "website-development")
    r = c.post("/api/inquiries/", json={
        "service_id": service_id,
        "name": "Inquirer",
        "email": "inq@example.com",
        "phone": "+1234567890",
        "message": "I need a website fast.",
    })
    check("POST /api/inquiries/ (public)", r.status_code == 201,
          f"status={r.status_code} body={r.text[:200]}")

    r = c.get("/api/inquiries/admin/all", headers=admin_h)
    check("GET /api/inquiries/admin/all (admin)", r.status_code == 200 and len(r.json()) >= 1)

    r = c.get("/api/inquiries/admin/all", headers=auth_h)
    check("GET /api/inquiries/admin/all (non-admin) returns 403", r.status_code == 403)

    inq_id = r.json() if False else c.get("/api/inquiries/admin/all", headers=admin_h).json()[0]["id"]
    r = c.patch(f"/api/inquiries/admin/{inq_id}", json={"status": "contacted"}, headers=admin_h)
    check("PATCH /api/inquiries/admin/{id}", r.status_code == 200 and r.json()["status"] == "contacted")

    # ── Orders (customer) ─────────────────────────────────────────────────────
    lead_gen_id = next(s["id"] for s in services if s["slug"] == "lead-generation")
    r = c.post("/api/orders/", json={
        "service_id": lead_gen_id,
        "customer_notes": "Need 100 leads in fintech space",
    }, headers=auth_h)
    check("POST /api/orders/ (customer)", r.status_code == 201,
          f"status={r.status_code} body={r.text[:200]}")
    order = r.json()
    order_id = order["id"]
    check("Order has correct service", order["service"]["slug"] == "lead-generation")
    check("Order has user attached", order["user"]["email"] == user_email)

    r = c.get("/api/orders/my", headers=auth_h)
    check("GET /api/orders/my", r.status_code == 200 and len(r.json()) >= 1)

    r = c.get(f"/api/orders/{order_id}", headers=auth_h)
    check("GET /api/orders/{id} (own)", r.status_code == 200)

    # Other user shouldn't see it
    r = c.post("/api/auth/register", json={
        "email": f"other{suffix}@example.com", "full_name": "Other", "password": "Pass1234!"
    })
    other_token = r.json()["access_token"]
    r = c.get(f"/api/orders/{order_id}", headers={"Authorization": f"Bearer {other_token}"})
    check("GET /api/orders/{id} (other user) returns 403", r.status_code == 403)

    # Admin can see anyone's order
    r = c.get(f"/api/orders/{order_id}", headers=admin_h)
    check("GET /api/orders/{id} (admin sees any)", r.status_code == 200)

    # Admin updates status
    r = c.patch(f"/api/orders/{order_id}", json={"status": "in_progress", "admin_notes": "Started research"},
                headers=admin_h)
    check("PATCH /api/orders/{id} (admin)", r.status_code == 200 and r.json()["status"] == "in_progress")

    r = c.get("/api/orders/admin/all", headers=admin_h)
    check("GET /api/orders/admin/all (admin)", r.status_code == 200 and len(r.json()) >= 1)

    # ── Set order amount (admin) — the new endpoint we'll add ─────────────────
    r = c.patch(f"/api/orders/{order_id}", json={"amount": 500.0}, headers=admin_h)
    check("PATCH /api/orders/{id} — set amount (admin)", r.status_code == 200 and r.json()["amount"] == 500.0,
          f"status={r.status_code} body={r.text[:200]}")

    # ── Payments (bank transfer flow) ─────────────────────────────────────────
    r = c.get("/api/payments/bank-details")
    check("GET /api/payments/bank-details", r.status_code == 200 and "local" in r.json() and "international" in r.json(),
          f"status={r.status_code} body={r.text[:200]}")

    r = c.post("/api/payments/submit", json={
        "order_id": order_id,
        "payment_method": "bank_transfer",
        "transfer_reference": f"TXN-TEST-{suffix}",
        "notes": "Test transfer",
    }, headers=auth_h)
    check("POST /api/payments/submit (customer submits ref)",
          r.status_code == 200 and r.json()["payment_status"] == "awaiting_verification",
          f"status={r.status_code} body={r.text[:200]}")

    r = c.post(f"/api/payments/{order_id}/verify", json={"approve": True}, headers=admin_h)
    check("POST /api/payments/{id}/verify (admin approves)",
          r.status_code == 200 and r.json()["payment_status"] == "paid",
          f"status={r.status_code} body={r.text[:200]}")

    # Invoice PDF download (with ?token=...)
    r = c.get(f"/api/payments/{order_id}/invoice?token={auth_h['Authorization'].split()[1]}")
    check("GET /api/payments/{id}/invoice (PDF)",
          r.status_code == 200 and r.headers.get("content-type") == "application/pdf",
          f"status={r.status_code} content-type={r.headers.get('content-type')}")

    # ── Services CRUD (admin) ─────────────────────────────────────────────────
    test_slug = f"test-service-{suffix}"
    r = c.post("/api/services/", json={
        "name": "Test Service",
        "slug": test_slug,
        "short_description": "test",
        "full_description": "test long",
        "service_type": "fixed",
        "price": 99.0,
        "price_label": "$99",
        "features": "[]",
    }, headers=admin_h)
    check("POST /api/services/ (admin create)", r.status_code == 201,
          f"status={r.status_code} body={r.text[:200]}")
    new_svc_id = r.json()["id"]

    r = c.patch(f"/api/services/{new_svc_id}", json={"price": 149.0}, headers=admin_h)
    check("PATCH /api/services/{id} (admin update)", r.status_code == 200 and r.json()["price"] == 149.0)

    r = c.delete(f"/api/services/{new_svc_id}", headers=admin_h)
    check("DELETE /api/services/{id} (admin soft-delete)", r.status_code == 204)

    r = c.get(f"/api/services/{test_slug}")
    check("Soft-deleted service is hidden", r.status_code == 404)

    # ── Admin dashboard ───────────────────────────────────────────────────────
    r = c.get("/api/admin/stats", headers=admin_h)
    check("GET /api/admin/stats", r.status_code == 200 and "total_users" in r.json(),
          f"status={r.status_code} body={r.text[:200]}")
    stats = r.json()
    check("Stats include users count >= 2", stats["total_users"] >= 2)
    check("Stats include orders count >= 1", stats["total_orders"] >= 1)

    r = c.get("/api/admin/users", headers=admin_h)
    check("GET /api/admin/users", r.status_code == 200 and len(r.json()) >= 2)

    # Non-admin can't access
    r = c.get("/api/admin/stats", headers=auth_h)
    check("GET /api/admin/stats (non-admin) returns 403", r.status_code == 403)

    # ── Summary ───────────────────────────────────────────────────────────────
    passed = sum(results)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"  {passed}/{total} tests passed")
    print(f"{'='*60}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
