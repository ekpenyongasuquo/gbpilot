import csv

new_emails = {
    "Central": "owner@centralhtg.com",
    "Bell Dental Group": "laurie@belldentalgroup.com",
    "Right Way Heating & Cooling": "bill@rightwayhvac.com",
    "Gorjanc Home Services": "greg@gorjanc.com",
    "Dennison Dental Care": "tmartin@drkatya.com",
}

with open('data/leads.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

updated = 0
for row in rows:
    name = row.get('name', '').strip()
    for business_name, email in new_emails.items():
        if business_name.lower() in name.lower() or name.lower() in business_name.lower():
            if not row.get('email', '').strip():
                row['email'] = email
                row['email_confidence'] = '95'
                print(f"Updated: {name} -> {email}")
                updated += 1

with open('data/leads.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nTotal updated: {updated}")
print("leads.csv saved successfully")