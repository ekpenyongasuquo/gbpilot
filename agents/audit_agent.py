import os
import json
import datetime
from dotenv import load_dotenv
import google.auth
import google.auth.transport.requests
import requests

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
MODEL = os.getenv("GEMINI_MODEL")


def get_access_token():
    credentials, _ = google.auth.default()
    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)
    return credentials.token


def audit_business(business: dict) -> dict:
    """
    Takes a business dict with keys:
    name, address, rating, review_count, website, maps_url
    Returns an audit report with dollar-loss estimate.
    """
    prompt = f"""
You are a local SEO expert auditing a small business Google Business Profile.

Business Details:
- Name: {business.get('name')}
- Address: {business.get('address')}
- Rating: {business.get('rating')} stars
- Total Reviews: {business.get('review_count')}
- Website: {business.get('website', 'Not listed')}
- Google Maps URL: {business.get('maps_url')}

Return ONLY a valid JSON object with exactly these fields, no explanation, no markdown, no extra text:
{{
  "business_name": "string",
  "visibility_score": 45,
  "critical_issues": ["issue 1", "issue 2", "issue 3"],
  "estimated_monthly_searches_lost": 120,
  "estimated_monthly_revenue_lost_usd": 3500,
  "top_3_fixes": ["fix 1", "fix 2", "fix 3"],
  "audit_summary": "Two sentence plain English summary for the business owner."
}}

IMPORTANT: Return raw JSON only. No ```json tags. No markdown. No explanation before or after.
"""

    token = get_access_token()
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}"
        f"/locations/{LOCATION}/publishers/google/models/{MODEL}:generateContent"
    )

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json"
        }
    }

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    result = response.json()

    # Debug: show raw response if something goes wrong
    if "candidates" not in result:
        print(f"  Unexpected API response: {result}")
        raise ValueError("No candidates in API response")

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]

    # Aggressive JSON cleaning
    clean = raw_text.strip()
    if "```" in clean:
        parts = clean.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                clean = part
                break
    clean = clean.strip("`").strip()

    # Find JSON boundaries
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        clean = clean[start:end]

    try:
        audit = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"  Raw response was: {clean[:300]}")
        raise e

    return audit


def log_agent_decision(business_name: str, audit: dict):
    """
    Writes agent decision to a log file for judge submission evidence.
    """
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "agent": "AuditAgent",
        "input_business": business_name,
        "decision": {
            "visibility_score": audit.get("visibility_score"),
            "revenue_lost_usd": audit.get("estimated_monthly_revenue_lost_usd"),
            "issues_found": len(audit.get("critical_issues", [])),
            "action": "audit_complete"
        },
        "output": audit
    }

    os.makedirs("logs", exist_ok=True)
    with open("logs/agent_decisions.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"  [LOG] Decision recorded for {business_name}")


if __name__ == "__main__":
    # Test with a sample business
    test_business = {
        "name": "Smith Family Dental",
        "address": "123 Main St, Columbus, Ohio",
        "rating": 3.8,
        "review_count": 24,
        "website": "smithfamilydental.com",
        "maps_url": "https://maps.google.com/?cid=123456"
    }

    print("Running audit agent on test business...")
    print(f"Business: {test_business['name']}")
    print(f"Location: {test_business['address']}")
    print("-" * 50)

    audit = audit_business(test_business)

    print(json.dumps(audit, indent=2))
    print("-" * 50)

    log_agent_decision(test_business["name"], audit)

    print("\nSUMMARY FOR OWNER:")
    print(f"Visibility Score:              {audit.get('visibility_score')}/100")
    print(f"Monthly Revenue Lost:          ${audit.get('estimated_monthly_revenue_lost_usd'):,}")
    print(f"Top Fix:                       {audit.get('top_3_fixes', [''])[0]}")
    print(f"Summary:                       {audit.get('audit_summary')}")
