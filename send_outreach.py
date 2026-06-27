import csv
import time
import json
import os
from agents.audit_agent import audit_business, log_agent_decision
from utils.report_generator import generate_audit_report
from utils.outreach import send_audit_email
from dotenv import load_dotenv

load_dotenv()


def get_already_sent():
    """
    Returns set of emails already contacted.
    Prevents sending duplicate emails to same address.
    """
    sent = set()
    log_file = "logs/outreach_log.jsonl"
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


def send_to_real_businesses():
    """
    Sends real cold outreach emails to businesses
    that have email addresses in leads.csv.
    Skips businesses already contacted.
    """
    # Load all businesses with emails
    businesses_with_email = []
    with open("data/leads.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("email", "").strip():
                businesses_with_email.append(row)

    print(f"Found {len(businesses_with_email)} businesses with emails")

    # Get already contacted emails
    already_sent = get_already_sent()
    print(f"Already contacted: {len(already_sent)} emails")
    print("=" * 60)

    sent = 0
    skipped = 0
    failed = 0

    for i, business in enumerate(businesses_with_email):
        email = business.get("email", "").strip().lower()
        name = business.get("name", "")

        print(f"\n[{i+1}/{len(businesses_with_email)}] {name}")
        print(f"  Email: {email}")

        # Skip if already contacted
        if email in already_sent:
            print(f"  [SKIP] Already contacted — skipping")
            skipped += 1
            continue

        print(f"  Address: {business.get('address', '')}")

        try:
            # Run audit
            print(f"  Running AI audit...")
            audit = audit_business(business)
            log_agent_decision(name, audit)

            print(f"  Visibility Score: {audit.get('visibility_score')}/100")
            print(f"  Revenue Lost: ${audit.get('estimated_monthly_revenue_lost_usd'):,}")

            # Generate report
            report_path = generate_audit_report(business, audit)

            # Send email
            success = send_audit_email(business, audit, report_path)

            if success:
                print(f"  ✅ Email sent successfully")
                sent += 1
                # Add to already sent immediately
                already_sent.add(email)
            else:
                print(f"  ❌ Email failed")
                failed += 1

            # Wait between sends to avoid spam flags
            time.sleep(3)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"OUTREACH COMPLETE")
    print(f"✅ Sent:    {sent}")
    print(f"⏭️  Skipped: {skipped} (already contacted)")
    print(f"❌ Failed:  {failed}")
    print(f"Log saved to: logs/outreach_log.jsonl")
    print("=" * 60)

    # Save outreach summary
    os.makedirs("data", exist_ok=True)
    with open("data/outreach_summary.json", "w") as f:
        json.dump({
            "total_sent": sent,
            "total_skipped": skipped,
            "total_failed": failed,
            "total_businesses": len(businesses_with_email)
        }, f, indent=2)


if __name__ == "__main__":
    send_to_real_businesses()