import csv

new_emails = {
    "Seven Star Dental": "info@sevenstardental.com",
    "Weber Road Auto Service": "info@weberroadauto.com",
    "Beachwood Dental": "info@beachwooddental.com",
    "Pearce Dental Group of Cincinnati, OH": "info@pearcedentalgroup.com",
    "Hudec Dental": "jdevera@hudecdental.com",
    "Columbus Worthington Air": "dmarshall@cwaohio.com",
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
                row['email_confidence'] = '90'
                print(f"Updated: {name} -> {email}")
                updated += 1

with open('data/leads.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nTotal updated: {updated}")