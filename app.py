import os
import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from agents.audit_agent import audit_business, log_agent_decision
from utils.gbp_scraper import scrape_businesses

load_dotenv()

app = FastAPI(title="GBPilot API")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/audit")
async def run_audit(request: Request):
    body = await request.json()
    name = body.get("name", "")
    city = body.get("city", "")
    email = body.get("email", "")

    # Search for the business on Google Maps
    from utils.gbp_scraper import scrape_businesses
    businesses = scrape_businesses(
        queries=[f"{name} in {city}"],
        output_file="data/live_leads.csv"
    )

    if not businesses:
        # Fallback: create a basic business dict from form input
        business = {
            "name": name,
            "address": city,
            "rating": 3.5,
            "review_count": 15,
            "website": "",
            "maps_url": ""
        }
    else:
        business = businesses[0]

    # Run audit agent
    audit = audit_business(business)
    log_agent_decision(name, audit)

    # Log the lead email
    os.makedirs("data", exist_ok=True)
    with open("data/leads_email.jsonl", "a") as f:
        f.write(json.dumps({
            "name": name,
            "city": city,
            "email": email,
            "audit_score": audit.get("visibility_score"),
            "revenue_lost": audit.get("estimated_monthly_revenue_lost_usd")
        }) + "\n")

    return JSONResponse({
        "visibility_score": audit.get("visibility_score"),
        "revenue_lost": audit.get("estimated_monthly_revenue_lost_usd"),
        "searches_lost": audit.get("estimated_monthly_searches_lost"),
        "issues": audit.get("critical_issues", []),
        "fixes": audit.get("top_3_fixes", []),
        "summary": audit.get("audit_summary")
    })

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "GBPilot Audit Agent", "model": "gemini-2.5-flash"}