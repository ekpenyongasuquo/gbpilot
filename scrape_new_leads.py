from utils.gbp_scraper import scrape_businesses

print("Scraping new cities for fresh leads...")

businesses = scrape_businesses(
    queries=[
        "dentist in Indianapolis Indiana",
        "dentist in Louisville Kentucky",
        "auto repair in Indianapolis Indiana",
        "HVAC repair in Louisville Kentucky",
        "dentist in Nashville Tennessee",
        "auto repair in Nashville Tennessee",
        "HVAC repair in Indianapolis Indiana",
        "dentist in Cincinnati Ohio",
        "auto repair shop in Louisville Kentucky",
        "HVAC repair in Nashville Tennessee"
    ],
    output_file="data/new_leads.csv"
)

print(f"\nTotal new businesses scraped: {len(businesses)}")
print("Saved to data/new_leads.csv")
print("\nTop 10 hottest leads:")
for b in businesses[:10]:
    print(f"  {b['name']} | {b['address']} | Rating: {b['rating']} | Score: {b['lead_score']}")