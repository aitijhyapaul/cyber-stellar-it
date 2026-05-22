# Email Setup Guide — Cyber Stellar IT

Your services website is set up to send automated email notifications for inquiries and orders. To enable email:

## Quick Setup (5 minutes)

### 1. Enable 2-Factor Authentication on Gmail
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Click "2-Step Verification" and follow the prompts
3. Verify your phone number and enable it

### 2. Create a Gmail App Password
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select **Mail** and **Windows Computer** (or your device)
3. Google will generate a 16-character password
4. **Copy this password** (it includes spaces)

### 3. Update Your Backend .env File
Open `services-website/backend/.env` and update this line:
```
SMTP_PASSWORD=your-gmail-app-password-here
```

Replace `your-gmail-app-password-here` with the 16-character password you just created. Include the spaces.

Example:
```
SMTP_PASSWORD=abcd efgh ijkl mnop
```

### 4. Restart the Backend Server
Stop and restart the `csit-site` server in Claude Code to load the new environment variables.

## What Gets Emailed

### Inquiry Forms (Main Site Contact)
- **Customer receives**: "We Got Your Inquiry!" confirmation
- **Admin receives**: New inquiry alert with message details

### Lead Orders (Leads Landing Page)
- **Customer receives**: Order confirmation with order ID
- **Admin receives**: New order alert with targeting details

### Service Orders (After Stellar/Service Signup)
- **Customer receives**: Order confirmation
- **Admin receives**: New order alert

## Testing Email

1. Fill out the contact form on the main site at `localhost:8100`
2. Check your inbox for a confirmation email from `Cyber Stellar IT`
3. Check the admin email (aitijhyapaul@gmail.com) for the alert

## Troubleshooting

**Emails not sending?**
- Check that SMTP_PASSWORD is exactly as Google provided (with spaces)
- Make sure 2-Factor Authentication is enabled on your Gmail account
- Restart the backend server after updating .env
- Check backend logs for email errors

**Getting "password incorrect" error?**
- App passwords work differently than your regular Gmail password
- Create a NEW app password, don't use your Gmail password
- Make sure you copied it exactly, including spaces

**Testing without email setup:**
- Leave SMTP_USER and SMTP_PASSWORD blank
- Emails will log to console instead: `[EMAIL SKIPPED]`
- Useful for local development without Gmail credentials

## Production Deployment

When deploying to a real domain (cyberstellarbd.com):
1. Use the same Gmail credentials OR switch to a business email service
2. Store secrets in your hosting platform's environment variables (not .env)
3. Update FRONTEND_ORIGINS in .env to your real domain
4. Never commit .env to version control (it's already in .gitignore)

---

**Questions?** Check `services-website/backend/email_service.py` for implementation details.
