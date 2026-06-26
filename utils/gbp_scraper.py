import os
import requests
import csv
import time
from dotenv import load_dotenv

load_dotenv()

MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

SEARCH_QUERIES = [
    "dentist in Columbus Ohio",
    "dentist in Cleveland Ohio",
    "dentist in Cincinnati Ohio",
    "HVAC repair in Columbus Ohio",
    "HVAC repair in Cleveland Ohio",
    "auto repair shop in Columbus Ohio",
    "auto repair shop in Cincinnati Ohio",
]

def scrape_businesses(queries: list = None, output_file: str = "data/leads.csv") -> list:
    """
    Scrapes Google Maps for businesses matching the queries.
    Scores them by review count and rating.
    Saves results to leads.csv.
    Returns list of business dicts.
    """
    if queries is None:
        queries = SEARCH_QUERIES

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": MAPS_API_KEY,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.rating,"
            "places.userRatingCount,"
            "places.websiteUri,"
            "places.googleMapsUri,"
            "places.businessStatus"
        )
    }

    all_businesses = []
    seen = set()

    for query in queries:
        print(f"Scraping: {query}")
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"textQuery": query}
            )
            data = response.json()

            for place in data.get("places", []):
                name = place.get("displayName", {}).get("text", "")
                address = place.get("formattedAddress", "")

                # Deduplicate by name + address
                key = f"{name}_{address}"
                if key in seen:
                    continue
                seen.add(key)

                business = {
                    "name": name,
                    "address": address,
                    "rating": place.get("rating", 0),
                    "review_count": place.get("userRatingCount", 0),
                    "website": place.get("websiteUri", ""),
                    "maps_url": place.get("googleMapsUri", ""),
                    "status": place.get("businessStatus", ""),
                    "lead_score": calculate_lead_score(
                        place.get("rating", 0),
                        place.get("userRatingCount", 0)
                    )
                }
                all_businesses.append(business)

        except Exception as e:
            print(f"Error scraping '{query}': {e}")

        time.sleep(1)

    # Sort by lead score descending (hottest leads first)
    all_businesses.sort(key=lambda x: x["lead_score"], reverse=True)

    # Save to CSV
    os.makedirs("data", exist_ok=True)
    if all_businesses:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_businesses[0].keys())
            writer.writeheader()
            writer.writerows(all_businesses)
        print(f"\nSaved {len(all_businesses)} businesses to {output_file}")

    return all_businesses


def calculate_lead_score(rating: float, review_count: int) -> float:
    """
    Higher score = hotter lead (more visible gap to fix).
    Low review count + low rating = biggest opportunity.
    """
    rating_gap = max(0, 5.0 - float(rating)) * 20
    review_gap = max(0, 100 - int(review_count)) * 0.5
    return round(rating_gap + review_gap, 2)


if __name__ == "__main__":
    print("Starting Google Maps scrape...")
    businesses = scrape_businesses()
    print(f"\nTop 5 hottest leads:")
    for b in businesses[:5]:
        print(f"  {b['name']} | Rating: {b['rating']} | Reviews: {b['review_count']} | Score: {b['lead_score']}")