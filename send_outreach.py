import csv
import time
import json
import os
from agents.audit_agent import audit_business, log_agent_decision
from utils.report_generator import generate_audit_report
from utils.outreach import send_audit_email
from dotenv import load_dotenv

load_dotenv()


def send_to_real_businesses():
    """
    Sends real cold outreach emails to businesses
    that have email addresses in leads.csv
    """
    businesses_with_email = []

    with open("data/leads.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("email", "").strip():
                businesses_with_email.append(row)

    print(f"Found {len(businesses_with_email)} businesses with emails")
    print("=" * 60)

    sent = 0
    failed = 0

    for i, business in enumerate(businesses_with_email):
        print(f"\n[{i+1}/{len(businesses_with_email)}] {business['name']}")
        print(f"  Email: {business['email']}")
        print(f"  Address: {business['address']}")

        try:
            # Run audit
            print(f"  Running AI audit...")
            audit = audit_business(business)
            log_agent_decision(business["name"], audit)

            print(f"  Visibility Score: {audit.get('visibility_score')}/100")
            print(f"  Revenue Lost: ${audit.get('estimated_monthly_revenue_lost_usd'):,}")

            # Generate report
            report_path = generate_audit_report(business, audit)

            # Send email
            success = send_audit_email(business, audit, report_path)

            if success:
                print(f"  ✅ Email sent successfully")
                sent += 1
            else:
                print(f"  ❌ Email failed — no email address")
                failed += 1

            # Wait between sends to avoid spam flags
            time.sleep(3)

        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"OUTREACH COMPLETE")
    print(f"✅ Sent: {sent}")
    print(f"❌ Failed/Skipped: {failed}")
    print(f"Log saved to: logs/outreach_log.jsonl")
    print("=" * 60)

    # Save outreach summary
    os.makedirs("data", exist_ok=True)
    with open("data/outreach_summary.json", "w") as f:
        json.dump({
            "total_sent": sent,
            "total_failed": failed,
            "total_businesses": len(businesses_with_email)
        }, f, indent=2)


if __name__ == "__main__":
    send_to_real_businesses()