import os
import json
import smtplib
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from agents.audit_agent import audit_business, log_agent_decision
from utils.report_generator import generate_audit_report

load_dotenv()

SENDER_EMAIL = os.getenv("OUTREACH_EMAIL")
SENDER_PASSWORD = os.getenv("OUTREACH_PASSWORD")
GBPILOT_URL = "https://gbpilot.onrender.com"


def send_audit_email(business: dict, audit: dict, report_path: str) -> bool:
    """
    Sends a personalized cold outreach email to a business
    with their audit report attached.
    """
    recipient_email = business.get("email", "")
    if not recipient_email:
        print(f"  [SKIP] No email for {business.get('name')}")
        return False

    business_name = business.get("name", "")
    revenue_lost = audit.get("estimated_monthly_revenue_lost_usd", 0)
    visibility_score = audit.get("visibility_score", 0)
    top_fix = audit.get("top_3_fixes", [""])[0]
    issue_1 = audit.get("critical_issues", [""])[0]

    subject = f"Your Google listing is losing ${revenue_lost:,}/month — free fix inside"

    body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px;">

<p>Hi {business_name} team,</p>

<p>I ran a quick AI audit on your Google Business Profile and found something worth flagging.</p>

<p style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; border-radius: 4px;">
  <strong>Your listing scored {visibility_score}/100 on local visibility</strong> — which means 
  you're likely missing out on an estimated <strong>${revenue_lost:,} in revenue every month</strong> 
  from customers searching Google for businesses like yours.
</p>

<p>The biggest issue we found:</p>
<p style="background: #f8fafc; padding: 12px; border-radius: 4px;">
  ⚠️ {issue_1}
</p>

<p>The top fix:</p>
<p style="background: #f0fdf4; padding: 12px; border-radius: 4px;">
  ✅ {top_fix}
</p>

<p>I've attached your full AI audit report (it takes 30 seconds to read) — it breaks down 
exactly what's hurting your ranking and what fixes would have the biggest impact.</p>

<p>
  <a href="{GBPILOT_URL}" 
     style="background: #1e40af; color: white; padding: 12px 24px; 
            border-radius: 8px; text-decoration: none; font-weight: bold;">
    See Your Full Audit Report →
  </a>
</p>

<p>If you want GBPilot to handle all of this automatically — posts, fixes, monitoring — 
it's <strong>$79/month per location</strong>, and the first 7 days are free.</p>

<p>Happy to answer any questions.</p>

<p>Best,<br>
<strong>Ekpenyong Mfon</strong><br>
GBPilot — AI-Powered Google Business Profile Management<br>
<a href="{GBPILOT_URL}">{GBPILOT_URL}</a>
</p>

<p style="font-size: 11px; color: #94a3b8; margin-top: 20px;">
You're receiving this because GBPilot's AI audited publicly available Google Business Profile data 
for businesses in your area. To unsubscribe, reply with "unsubscribe".
</p>

</body>
</html>
"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email

        msg.attach(MIMEText(body, 'html'))

        # Attach the HTML audit report
        with open(report_path, 'rb') as f:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="GBPilot_Audit_{business_name.replace(" ", "_")}.html"'
            )
            msg.attach(attachment)

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())

        print(f"  [EMAIL] Sent to {recipient_email}")

        # Log the outreach
        os.makedirs("logs", exist_ok=True)
        with open("logs/outreach_log.jsonl", "a") as f:
            f.write(json.dumps({
                "business": business_name,
                "email": recipient_email,
                "subject": subject,
                "audit_score": visibility_score,
                "revenue_lost": revenue_lost,
                "status": "sent"
            }) + "\n")

        return True

    except Exception as e:
        print(f"  [ERROR] Failed to send to {recipient_email}: {e}")
        return False


def run_outreach_pipeline(leads_file: str = "data/leads.csv", limit: int = 20):
    """
    Runs the full outreach pipeline:
    1. Load leads from CSV
    2. Audit each business
    3. Generate report
    4. Send personalized email
    """
    print("=" * 60)
    print("GBPILOT OUTREACH PIPELINE")
    print("=" * 60)

    # Load leads
    businesses = []
    with open(leads_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            businesses.append(row)

    print(f"Loaded {len(businesses)} leads from {leads_file}")

    # Filter businesses that have emails
    # Note: Google Maps doesn't return emails directly
    # You'll need to manually add emails to leads.csv
    # or use a tool like Hunter.io to find them
    targets = businesses[:limit]

    sent = 0
    failed = 0

    for i, business in enumerate(targets):
        print(f"\n[{i+1}/{limit}] Processing: {business['name']}")

        if not business.get("email"):
            print(f"  [SKIP] No email address — add manually to leads.csv")
            continue

        try:
            # Audit
            audit = audit_business(business)
            log_agent_decision(business["name"], audit)

            # Generate report
            report_path = generate_audit_report(business, audit)

            # Send email
            success = send_audit_email(business, audit, report_path)
            if success:
                sent += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"OUTREACH COMPLETE")
    print(f"Sent: {sent} | Failed/Skipped: {failed}")
    print(f"Log saved to: logs/outreach_log.jsonl")
    print("=" * 60)


if __name__ == "__main__":
    run_outreach_pipeline(limit=20)