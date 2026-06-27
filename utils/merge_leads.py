import csv
import os

def merge_hunter_leads(
    leads_file="data/leads.csv",
    hunter_file="data/hunter_leads.csv",
    output_file="data/leads.csv"
):
    """
    Merges Hunter.io email contacts into leads.csv
    Matches by company website domain
    Picks the highest confidence score email per company
    Skips duplicates
    """

    # Load Hunter leads - group by website domain
    hunter_by_domain = {}
    with open(hunter_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row.get("Website", "").strip().lower()
            email = row.get("Email address", "").strip()
            confidence = int(row.get("Confidence score", 0) or 0)
            name = row.get("Full name", "").strip()
            job_title = row.get("Job title", "").strip()

            if not domain or not email:
                continue

            # Keep highest confidence email per domain
            if domain not in hunter_by_domain:
                hunter_by_domain[domain] = {
                    "email": email,
                    "confidence": confidence,
                    "contact_name": name,
                    "contact_title": job_title
                }
            elif confidence > hunter_by_domain[domain]["confidence"]:
                hunter_by_domain[domain] = {
                    "email": email,
                    "confidence": confidence,
                    "contact_name": name,
                    "contact_title": job_title
                }

    print(f"Hunter leads loaded: {len(hunter_by_domain)} unique domains")
    for domain, data in hunter_by_domain.items():
        print(f"  {domain} → {data['email']} ({data['confidence']}% confidence)")

    # Load existing leads
    leads = []
    with open(leads_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            leads.append(row)

    # Add new columns if not present
    new_fields = ["email", "contact_name", "contact_title", "email_confidence"]
    for field in new_fields:
        if field not in fieldnames:
            fieldnames = list(fieldnames) + [field]

    # Match and merge
    matched = 0
    for lead in leads:
        website = lead.get("website", "").strip().lower()

        # Extract clean domain from website URL
        domain = website
        for prefix in ["https://www.", "http://www.", "https://", "http://"]:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        domain = domain.split("/")[0].split("?")[0].strip()

        if domain in hunter_by_domain:
            hunter_data = hunter_by_domain[domain]
            if not lead.get("email"):
                lead["email"] = hunter_data["email"]
                lead["contact_name"] = hunter_data["contact_name"]
                lead["contact_title"] = hunter_data["contact_title"]
                lead["email_confidence"] = hunter_data["confidence"]
                matched += 1
                print(f"  MATCHED: {lead['name']} → {hunter_data['email']}")

    # Also add Hunter leads that didn't match existing leads
    # (new businesses not in our scraped list)
    existing_domains = set()
    for lead in leads:
        website = lead.get("website", "").strip().lower()
        domain = website
        for prefix in ["https://www.", "http://www.", "https://", "http://"]:
            if domain.startswith(prefix):
                domain = domain[len(prefix):]
        domain = domain.split("/")[0].split("?")[0].strip()
        existing_domains.add(domain)

    new_added = 0
    for domain, data in hunter_by_domain.items():
        if domain not in existing_domains:
            new_lead = {field: "" for field in fieldnames}
            new_lead["name"] = domain
            new_lead["website"] = f"https://{domain}"
            new_lead["email"] = data["email"]
            new_lead["contact_name"] = data["contact_name"]
            new_lead["contact_title"] = data["contact_title"]
            new_lead["email_confidence"] = data["confidence"]
            leads.append(new_lead)
            new_added += 1
            print(f"  NEW: {domain} → {data['email']}")

    # Save updated leads
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)

    print(f"\n{'='*50}")
    print(f"MERGE COMPLETE")
    print(f"Leads matched with emails: {matched}")
    print(f"New leads added: {new_added}")
    print(f"Total leads in file: {len(leads)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    merge_hunter_leads()