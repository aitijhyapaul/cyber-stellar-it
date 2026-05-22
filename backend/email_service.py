import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
SITE_NAME = os.getenv("SITE_NAME", "My Services")


def _fmt_amount(amount: float, currency: str) -> str:
    cur = (currency or "bdt").lower()
    if cur == "usd":
        return f"${amount:,.2f} USD"
    return f"৳{amount:,.2f} BDT"


def _send(to: str, subject: str, html: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        print(f"[EMAIL SKIPPED] To: {to} | Subject: {subject}")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SITE_NAME} <{SMTP_USER}>"
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to, msg.as_string())
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


def send_order_confirmation(user_email: str, user_name: str, service_name: str, order_id: int):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2>Order Received!</h2>
      <p>Hi {user_name},</p>
      <p>Your order for <strong>{service_name}</strong> has been received (Order #{order_id}).</p>
      <p>Please complete payment via bank/wire transfer using the instructions on your invoice. After sending, submit the transfer reference on your dashboard so we can verify it.</p>
      <br><p>Thanks,<br><strong>{SITE_NAME}</strong></p>
    </div>
    """
    _send(user_email, f"Order #{order_id} Received – {service_name}", html)


def send_order_admin_alert(service_name: str, user_name: str, user_email: str, order_id: int, notes: str = ""):
    if not ADMIN_EMAIL:
        return
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2>New Order #{order_id}</h2>
      <p><strong>Service:</strong> {service_name}</p>
      <p><strong>Customer:</strong> {user_name} ({user_email})</p>
      <p><strong>Notes:</strong> {notes or 'None'}</p>
    </div>
    """
    _send(ADMIN_EMAIL, f"New Order #{order_id} – {service_name}", html)


def send_inquiry_confirmation(email: str, name: str, service_name: str = ""):
    service_line = f"regarding <strong>{service_name}</strong>" if service_name else ""
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2>We Got Your Inquiry!</h2>
      <p>Hi {name},</p>
      <p>Thanks for reaching out {service_line}. We'll get back to you within 24 hours.</p>
      <br><p>Thanks,<br><strong>{SITE_NAME}</strong></p>
    </div>
    """
    _send(email, "We received your inquiry", html)


def send_inquiry_admin_alert(name: str, email: str, message: str, service_name: str = ""):
    if not ADMIN_EMAIL:
        return
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2>New Inquiry</h2>
      <p><strong>From:</strong> {name} ({email})</p>
      <p><strong>Service:</strong> {service_name or 'General'}</p>
      <p><strong>Message:</strong> {message}</p>
    </div>
    """
    _send(ADMIN_EMAIL, f"New Inquiry from {name}", html)


# ── Bank-transfer payment flow emails ────────────────────────────────────────

def send_payment_submitted_admin_alert(
    user_name: str, user_email: str, order_id: int,
    service_name: str, amount: float, currency: str,
    transfer_ref: str, method: str,
):
    if not ADMIN_EMAIL:
        return
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2>Payment Submitted – Verify Now</h2>
      <p><strong>Order:</strong> #{order_id} – {service_name}</p>
      <p><strong>Customer:</strong> {user_name} ({user_email})</p>
      <p><strong>Amount:</strong> {_fmt_amount(amount, currency)}</p>
      <p><strong>Method:</strong> {method}</p>
      <p><strong>Transfer Ref:</strong> <code>{transfer_ref}</code></p>
      <p>Check your bank statement and verify in the admin dashboard.</p>
    </div>
    """
    _send(ADMIN_EMAIL, f"[Verify] Payment for Order #{order_id} ({transfer_ref})", html)


def send_payment_received_customer(user_email: str, user_name: str, order_id: int, transfer_ref: str):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2>Payment Reference Received</h2>
      <p>Hi {user_name},</p>
      <p>We've received your transfer reference <code>{transfer_ref}</code> for Order #{order_id}.</p>
      <p>Our team will verify the transfer against our bank statement, usually within 1 business day. You'll get an email as soon as it's confirmed.</p>
      <br><p>Thanks,<br><strong>{SITE_NAME}</strong></p>
    </div>
    """
    _send(user_email, f"Payment Reference Received – Order #{order_id}", html)


def send_payment_verified_customer(user_email: str, user_name: str, service_name: str, amount: float, currency: str, order_id: int):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2>✅ Payment Verified</h2>
      <p>Hi {user_name},</p>
      <p>Your payment of <strong>{_fmt_amount(amount, currency)}</strong> for <strong>{service_name}</strong> has been verified.</p>
      <p>Order #{order_id} is now active and we'll get started right away.</p>
      <br><p>Thanks,<br><strong>{SITE_NAME}</strong></p>
    </div>
    """
    _send(user_email, f"Payment Verified – Order #{order_id}", html)


def send_payment_rejected_customer(user_email: str, user_name: str, order_id: int, reason: str):
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2>Payment Verification Issue</h2>
      <p>Hi {user_name},</p>
      <p>We couldn't verify the transfer you submitted for Order #{order_id}.</p>
      <p><strong>Reason:</strong> {reason}</p>
      <p>Please double-check your bank record and re-submit the correct transfer reference, or contact us if you need help.</p>
      <br><p>Thanks,<br><strong>{SITE_NAME}</strong></p>
    </div>
    """
    _send(user_email, f"Payment Verification Issue – Order #{order_id}", html)


# Legacy alias kept so any older calls don't break (unused going forward)
def send_payment_receipt(user_email: str, user_name: str, service_name: str, amount: float, order_id: int):
    send_payment_verified_customer(user_email, user_name, service_name, amount, "bdt", order_id)
