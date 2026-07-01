import csv
import json

# Remove bounced email from leads.csv
with open('data/leads.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

# Debug - show all emails in file
print("All emails currently in leads.csv:")
for row in rows:
    if row.get('email', '').strip():
        print(f"  {row['name']} | {row['email']}")

# Remove bounced email
removed = False
for row in rows:
    email = row.get('email', '').strip().lower()
    if 'budgetohio' in email or 'mike@budget' in email:
        print(f"\nRemoving: {row['name']} | {row['email']}")
        row['email'] = ''
        removed = True

if not removed:
    print("\nEmail not found - may already be removed")

with open('data/leads.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print('\nDone')