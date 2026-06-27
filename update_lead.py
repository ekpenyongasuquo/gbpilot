import csv

# Read existing leads
with open('data/leads.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Find and update 4th St Dental Studio
for row in rows:
    if '4th St Dental Studio' in row.get('name', ''):
        row['email'] = 'frontdesk@4thstreetdentalstudio.com'
        row['contact_name'] = 'Front Desk'
        row['contact_title'] = 'Front Desk'
        row['email_confidence'] = '95'
        print(f"Updated: {row['name']} -> {row['email']}")

# Save back
with open('data/leads.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print('Done - leads.csv updated')