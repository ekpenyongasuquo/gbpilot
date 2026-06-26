import os
import json
import time
from dotenv import load_dotenv
from agents.audit_agent import audit_business, log_agent_decision
from utils.gbp_scraper import scrape_businesses
from utils.report_generator import generate_audit_report

load_dotenv()

def run_audit_pipeline(limit: int = 5):
    """
    Full pipeline:
    1. Scrape businesses from Google Maps
    2. Run audit agent on each
    3. Generate HTML report for each
    4. Log every decision
    5. Print summary report
    """
    print("=" * 60)
    print("GBPILOT AUDIT PIPELINE STARTING")
    print("=" * 60)

    # Step 1 - Scrape
    print("\nSTEP 1: Scraping target businesses...")
    businesses = scrape_businesses()

    if not businesses:
        print("No businesses found. Check your GOOGLE_MAPS_API_KEY in .env")
        return

    # Step 2 - Audit top leads
    targets = businesses[:limit]
    print(f"\nSTEP 2: Running Audit Agent on top {limit} leads...")

    results = []
    for i, business in enumerate(targets):
        print(f"\n[{i+1}/{limit}] Auditing: {business['name']}")
        try:
            audit = audit_business(business)
            log_agent_decision(business["name"], audit)

            # Step 3 - Generate report
            report_path = generate_audit_report(business, audit)

            results.append({
                "business": business,
                "audit": audit,
                "report_path": report_path
            })
            time.sleep(1)

        except Exception as e:
            print(f"  Error auditing {business['name']}: {e}")

    # Step 4 - Print summary
    print("\n" + "=" * 60)
    print("GBPILOT AUDIT REPORT SUMMARY")
    print("=" * 60)

    total_revenue_lost = 0
    for r in results:
        b = r["business"]
        a = r["audit"]
        revenue_lost = a.get("estimated_monthly_revenue_lost_usd", 0)
        total_revenue_lost += revenue_lost
        print(f"\n{b['name']}")
        print(f"  Address:               {b['address']}")
        print(f"  Visibility Score:      {a.get('visibility_score')}/100")
        print(f"  Monthly Revenue Lost:  ${revenue_lost:,}")
        print(f"  Top Fix:               {a.get('top_3_fixes', [''])[0]}")
        print(f"  Report:                {r['report_path']}")

    print(f"\nTOTAL ESTIMATED MONTHLY REVENUE LOST: ${total_revenue_lost:,}")
    print(f"REPORTS GENERATED: {len(results)}")
    print("\nAgent decision logs: logs/agent_decisions.jsonl")
    print("=" * 60)

    # Save full results
    os.makedirs("data", exist_ok=True)
    with open("data/audit_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("Full results saved to: data/audit_results.json")

    return results


if __name__ == "__main__":
    run_audit_pipeline(limit=5)