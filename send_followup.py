import csv
import json
import time
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("OUTREACH_EMAIL")
SENDER_PASSWORD = os.getenv("OUTREACH_PASSWORD")
GBPILOT_URL = "https://gbpilot.onrender.com"


def get_audit_data():
    """
    Loads audit results from logs to personalize follow-up emails.
    Returns dict keyed by business name.
    """
    audit_data = {}
    log_file = "logs/agent_decisions.jsonl"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    name = entry.get("input_business", "")
                    revenue_lost = entry.get("decision", {}).get("revenue_lost_usd", 0)
                    visibility_score = entry.get("decision", {}).get("visibility_score", 0)
                    if name and revenue_lost:
                        audit_data[name] = {
                            "revenue_lost": revenue_lost,
                            "visibility_score": visibility_score
                        }
                except Exception:
                    continue
    return audit_data


def get_already_followed_up():
    """
    Returns set of emails already sent follow-up to.
    Prevents duplicate follow-ups.
    """
    sent = set()
    log_file = "logs/followup_log.jsonl"
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    email = entry.get("email", "").strip().lower()
                    if email:
                        sent.add(email)
                except Exception:
                    continue
    return sent


def send_followup_email(business_name: str, email: str, revenue_lost: int) -> bool:
    """
    Sends personalized follow-up email to a business.
    """
    subject = "Special offer — first month of GBPilot for $29"

    body = f"""
<html>
<body style="font-family: Arial, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px;">

<p>Hi {business_name} team,</p>

<p>I reached out a few days ago with a free AI audit of your Google Business Profile.</p>

<p>I wanted to follow up with something specific: for businesses that sign up this week, 
I'm offering the first month of GBPilot at <strong>$29 instead of $79</strong> — 
no commitment, cancel anytime.</p>

<p>As a reminder, our AI audit found your listing is missing out on an estimated 
<strong>${revenue_lost:,} in monthly revenue</strong> from local searches.</p>

<p>What GBPilot does automatically every week:</p>
<ul style="color: #1e293b; line-height: 1.8;">
  <li>Publishes fresh Google Posts to keep your listing active</li>
  <li>Monitors your ranking against local competitors</li>
  <li>Flags profile issues before they hurt your visibility</li>
  <li>Answers customer Q&A on your listing automatically</li>
</ul>

<p>You can start your trial here in 2 minutes:</p>

<p>
  <a href="{GBPILOT_URL}" 
     style="background: #1e40af; color: white; padding: 12px 24px; 
            border-radius: 8px; text-decoration: none; font-weight: bold; display: inline-block;">
    Start for $29 This Week →
  </a>
</p>

<p>Happy to answer any questions — just reply to this email.</p>

<p>Best,<br>
<strong>Ekpenyong Mfon</strong><br>
GBPilot — AI-Powered Google Business Profile Management<br>
<a href="{GBPILOT_URL}">{GBPILOT_URL}</a>
</p>

<p style="font-size: 11px; color: #94a3b8; margin-top: 20px;">
To unsubscribe from future emails, reply with "unsubscribe".
</p>

</body>
</html>
"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = email

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())

        print(f"  ✅ Follow-up sent to {email}")

        # Log the follow-up
        os.makedirs("logs", exist_ok=True)
        with open("logs/followup_log.jsonl", "a") as f:
            f.write(json.dumps({
                "business": business_name,
                "email": email,
                "revenue_lost": revenue_lost,
                "subject": subject,
                "status": "sent"
            }) + "\n")

        return True

    except Exception as e:
        print(f"  ❌ Failed to send to {email}: {e}")
        return False


def run_followup_pipeline():
    """
    Sends personalized follow-up emails to all businesses
    that were previously contacted but haven't been followed up yet.
    """
    print("=" * 60)
    print("GBPILOT FOLLOW-UP PIPELINE")
    print("=" * 60)

    # Load audit data for personalization
    audit_data = get_audit_data()
    print(f"Audit data loaded for {len(audit_data)} businesses")

    # Get already followed up emails
    already_followed_up = get_already_followed_up()
    print(f"Already followed up: {len(already_followed_up)} emails")

    # Load leads with emails
    businesses = []
    with open("data/leads.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("email", "").strip():
                businesses.append(row)

    print(f"Total businesses with emails: {len(businesses)}")
    print("=" * 60)

    sent = 0
    skipped = 0
    failed = 0
    seen_emails = set()

    for business in businesses:
        email = business.get("email", "").strip().lower()
        name = business.get("name", "").strip()

        # Skip duplicates in the same run
        if email in seen_emails:
            continue
        seen_emails.add(email)

        # Skip already followed up
        if email in already_followed_up:
            print(f"[SKIP] Already followed up: {name}")
            skipped += 1
            continue

        # Get revenue lost from audit data
        revenue_lost = 3500  # default
        for audit_name, data in audit_data.items():
            if audit_name.lower() in name.lower() or name.lower() in audit_name.lower():
                revenue_lost = data.get("revenue_lost", 3500)
                break

        print(f"\n[FOLLOW-UP] {name}")
        print(f"  Email: {email}")
        print(f"  Revenue Lost: ${revenue_lost:,}")

        success = send_followup_email(name, email, revenue_lost)
        if success:
            sent += 1
            already_followed_up.add(email)
        else:
            failed += 1

        time.sleep(3)

    print("\n" + "=" * 60)
    print(f"FOLLOW-UP COMPLETE")
    print(f"✅ Sent:    {sent}")
    print(f"⏭️  Skipped: {skipped} (already followed up)")
    print(f"❌ Failed:  {failed}")
    print(f"Log saved to: logs/followup_log.jsonl")
    print("=" * 60)


if __name__ == "__main__":
    run_followup_pipeline()