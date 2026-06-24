from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import Optional, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Contraxa API is running"}


@app.get("/drug")
def get_drug(name: str):
    url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{name}&limit=1"

    response = requests.get(url)

    data = response.json()

    return data


def clean_ingredient_text(text: str):
    prefixes_to_remove = [
        "active ingredient", "active ingredients", "in each", "tablet", "purpose", ":"
    ]

    cleaned = text
    for prefix in prefixes_to_remove:
        cleaned = cleaned.lower().replace(prefix.lower(), "")

    return cleaned.strip().capitalize()


def extract_side_effects(text: str):
    if not text or text == "None listed":
        return []

    skip_phrases = ["see ", "report", "contact", "discussed in", "adverse reactions"]

    import re

    candidates = re.split(r'[,.:]', text)

    side_effects = []

    for candidate in candidates:
        candidate = candidate.strip()

        if 4 < len(candidate) < 60 and not any(skip in candidate.lower() for skip in skip_phrases):
            if not re.search(r'\(\s*\d', candidate):
                side_effects.append(candidate.capitalize())

    return side_effects[:7]


def fetch_drug_data(drug_name: str):
    url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug_name}&limit=1"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()

    if not data.get("results"):
        return None

    result = data["results"][0]

    purpose = result.get("purpose") or result.get("indications_and_usage") or ["Unknown"]

    active_ingredients = result.get("active_ingredient")
    if not active_ingredients:
        openfda_data = result.get("openfda", {})
        active_ingredients = openfda_data.get("generic_name") or openfda_data.get("substance_name") or ["Unknown"]

    warnings = result.get("warnings") or result.get("warnings_and_cautions") or ["None available"]

    return {
        "name": drug_name,
        "purpose": purpose[0],
        "active_ingredients": clean_ingredient_text(active_ingredients[0]),
        "warnings": warnings[0],
        "boxed_warning": result.get("boxed_warning", [None])[0],
        "side_effects": extract_side_effects(result.get("adverse_reactions", ["None listed"])[0])
    }

@app.get("/interact")
def check_interactions(drugs: List[str] = Query(...)):

    if len(drugs) != 2:
        return {"error": "v1 only supports checking exactly two drugs at a time"}

    drug_a, drug_b = drugs

    data_a = fetch_drug_data(drug_a)
    data_b = fetch_drug_data(drug_b)

    if data_a is None or data_b is None:
        return {"error": f"Could not find drug data for one or both: {drug_a}, {drug_b}"}

    # TODO: swap this placeholder for a real call into interactions.py
    # once the DrugInteraction table exists and is loaded from DDInter.
    interaction = {
        "status": "not_yet_implemented",
        "message": "Severity lookup is being migrated to DDInter -- coming next."
    }

    return {
        "interaction": interaction,
        "drugs": [data_a, data_b]
    }