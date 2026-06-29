import csv

# New emails found via Hunter Domain Search
new_emails = {
    "4th St Dental Studio": "frontdesk@4thstreetdentalstudio.com",
    "Advanced Dental Center": "drglenn@bestclevelandsmiles.com",
    "Dor-Mar Columbus Heating And Air": "customerservice@dormarhvac.com",
    "Capital City Dental": "smiles@capitalcitydental.com",
    "Conserv-Air": "mike@conserv-air.com",
    "Budget Heating and Air Conditioning": "mike@budgetohio.com",
    "Westar Dental - Westerville": "info@westardental.com",
    "Mt. Lookout Dentistry": "page@mtlookoutdentistry.com",
    "Hetter Heating & Cooling": "mike@hetterheating.com",
    "K and K Heating and Cooling": "info@kandkheatingandcooling.com",
}

# Read existing leads
with open('data/leads.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Update matching rows
updated = 0
for row in rows:
    name = row.get('name', '').strip()
    for business_name, email in new_emails.items():
        if business_name.lower() in name.lower() or name.lower() in business_name.lower():
            if not row.get('email', '').strip():
                row['email'] = email
                row['email_confidence'] = '99'
                print(f"Updated: {name} -> {email}")
                updated += 1

# Save back
with open('data/leads.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nTotal updated: {updated}")
print("leads.csv saved successfully")