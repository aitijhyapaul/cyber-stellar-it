# Services Website — Backend

FastAPI backend for the services showcase site (Website Development, SaaS ERP, Digital Marketing, Lead Generation).

## Stack
- **FastAPI** + **SQLAlchemy 2** — API + ORM (SQLite locally, Postgres in production)
- **Stripe** — payments
- **PyJWT** + **bcrypt** — auth
- **Gmail SMTP** — email notifications

## Quick Start (local)

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env       # fill in values (or leave Stripe/SMTP blank to skip)
python seed.py               # creates DB + 4 services + admin user
python -m uvicorn main:app --host 127.0.0.1 --port 8100 --reload
```

Or just double-click `run_dev.bat`.

- API docs: http://127.0.0.1:8100/api/docs
- Health: http://127.0.0.1:8100/api/health

> **Port 8100** is intentional — avoids clashing with your other FastAPI projects (Atashi ERP, ERP SaaS) which use 8000.

## Run the test suite

```powershell
# In one terminal: server running on 8100
# In another:
cd backend
venv\Scripts\python test_e2e.py
# Expect: 38/38 tests passed
```

## Default admin credentials (change these!)

After running `seed.py`:
- email: `admin@example.com`
- password: `changeme123`

Override by setting `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env` **before** running seed.

## Order Flow

For **fixed-price** services (Lead Generation):
1. Customer registers → places order → pays via Stripe → done.

For **quote** services (Website Dev, Digital Marketing, ERP):
1. Customer submits an **inquiry** (no auth needed).
2. Admin contacts them, agrees a price.
3. Customer registers and places an order (amount: null at first).
4. Admin sets the amount: `PATCH /api/orders/{id}` with `{"amount": 1500.0}`.
5. Customer pays via Stripe.

## Environment Variables

| Variable | Required? | What for |
|---|---|---|
| `SECRET_KEY` | Production | JWT signing — long random string |
| `DATABASE_URL` | Production | Postgres URL (blank → SQLite locally) |
| `STRIPE_SECRET_KEY` | For payments | From Stripe dashboard (use `sk_test_*` first) |
| `STRIPE_WEBHOOK_SECRET` | For payments | Required in production — set after creating webhook in Stripe |
| `ALLOW_UNSIGNED_WEBHOOKS` | Dev only | Set `1` to test webhooks locally without signatures |
| `SMTP_USER`, `SMTP_PASSWORD` | For email | Gmail address + **App Password** (not your real password) |
| `ADMIN_EMAIL` | For email | Where order/inquiry alerts go |
| `SITE_NAME` | Cosmetic | Shows up in email subject/footer |
| `FRONTEND_ORIGINS` | Production | Comma-separated allowed origins (`*` for dev) |
| `ADMIN_PASSWORD` | Pre-seed | Password for the seeded admin |
| `PORT` | Deploy | Set automatically by Railway/Render |

## Gmail App Password

To send emails:
1. Google Account → Security → enable 2-Step Verification
2. → App passwords → create one for "Mail"
3. Use the 16-character password as `SMTP_PASSWORD`

If `SMTP_USER`/`SMTP_PASSWORD` are blank, emails are skipped (logged to console as `[EMAIL SKIPPED]`).

## Deploy to Railway

1. Push repo to GitHub
2. Railway → New Project → Deploy from GitHub → pick repo
3. Add a Postgres database (creates `DATABASE_URL` automatically)
4. In Variables: set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `SECRET_KEY`, `SMTP_USER`, `SMTP_PASSWORD`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `SITE_NAME`
5. Railway reads `railway.json` and runs `seed.py` then starts uvicorn

## Deploy to Render

1. Push repo to GitHub
2. Render → New → "Web Service" → existing repo
3. Render reads `render.yaml`, creates a Postgres DB + web service
4. Set the `sync: false` env vars manually in the Render dashboard

## API Endpoints

### Public
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/services/` | List all active services |
| GET | `/api/services/{slug}` | Get one service |
| POST | `/api/inquiries/` | Submit inquiry (no auth) |
| POST | `/api/auth/register` | Register customer |
| POST | `/api/auth/login` | Login |

### Customer (auth required)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/auth/me` | Current user |
| POST | `/api/orders/` | Create order |
| GET | `/api/orders/my` | My orders |
| GET | `/api/orders/{id}` | Get my order |
| POST | `/api/payments/create-intent` | Stripe payment intent |

### Admin (admin token required)
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/admin/stats` | Dashboard stats |
| GET | `/api/admin/users` | All users |
| PATCH | `/api/admin/users/{id}/toggle-active` | Suspend/activate user |
| PATCH | `/api/admin/users/{id}/make-admin` | Promote to admin |
| GET | `/api/orders/admin/all` | All orders |
| PATCH | `/api/orders/{id}` | Update status / amount / notes |
| GET | `/api/inquiries/admin/all` | All inquiries |
| PATCH | `/api/inquiries/admin/{id}` | Update inquiry status |
| POST | `/api/services/` | Create new service |
| PATCH | `/api/services/{id}` | Update service |
| DELETE | `/api/services/{id}` | Soft-delete service |

### Webhook
| POST | `/api/payments/webhook` | Stripe webhook — required for marking orders paid |

## File Tree

```
services-website/
├── backend/
│   ├── main.py              FastAPI app + CORS + static mount
│   ├── database.py          SQLAlchemy setup, .env loading
│   ├── models.py            User, Service, Order, Inquiry tables
│   ├── schemas.py           Pydantic request/response models
│   ├── auth.py              JWT + bcrypt helpers
│   ├── email_service.py     Gmail SMTP notifications
│   ├── seed.py              Run once to seed services + admin
│   ├── test_e2e.py          End-to-end test suite (38 tests)
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── services_routes.py
│   │   ├── orders_routes.py
│   │   ├── payments_routes.py
│   │   ├── inquiries_routes.py
│   │   └── admin_routes.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── Procfile
│   └── run_dev.bat          Double-click to start dev server
├── railway.json
├── render.yaml
└── README.md
```
