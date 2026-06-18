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

def analyze_interactions(drug_data: list):
    bleeding_keywords = [
        "bleeding", "blood thinning", "anticoagulant", "hemorrhage",
        "blood thinner", "nsaid", "bruising" # removed warfarin and aspirin
    ]

    heart_keywords = [
        "heart attack", "stroke", "blood pressure", "cardiac",
        "heart failure", "hypertension", "cardiovascular"
    ]

    organ_keywords = [
        "liver", "kidney", "hepatic", "renal", "cirrhosis"
    ]

    danger_keywords = [
        "fatal", "death", "life threatening", "major bleeding",
        "do not use", "contraindicated", "boxed warning", "black box"
    ]

    all_keyword_categories = bleeding_keywords + heart_keywords + organ_keywords + danger_keywords

    keyword_to_drugs = {}

    for drug in drug_data:
        drug_text = drug["warnings"].lower() + (
            drug["boxed_warning"].lower() if drug["boxed_warning"] is not None else ""
        )

        for keyword in all_keyword_categories:
            if keyword in drug_text and keyword != drug["name"].lower():
                if keyword in keyword_to_drugs:
                    keyword_to_drugs[keyword].append(drug["name"])
                else:
                    keyword_to_drugs[keyword] = [drug["name"]]
    
    overlap_bleeding = []
    overlap_heart = []
    overlap_organ = []
    overlap_danger = []

    for key, value in keyword_to_drugs.items():
        if len(value) >= 2:
            if key in bleeding_keywords:
                overlap_bleeding.append(key)
            if key in heart_keywords:
                overlap_heart.append(key)
            if key in organ_keywords:
                overlap_organ.append(key)
            if key in danger_keywords:
                overlap_danger.append(key)
    
    flags = []

    if overlap_bleeding:
        flags.append("bleeding risk detected")
    if overlap_heart:
        flags.append("cardiovascular risk detected")
    if overlap_organ:
        flags.append("liver or kidney stress detected")
    
    def extract_key_warning(text: str, keywords: list):
        sentences = text.split(".")

        for sentence in sentences:
            sentence = sentence.strip()

            if any(kw in sentence.lower() for kw in keywords):
                if 20 < len(sentence) < 300:
                    return sentence + "."
        
        return None
    
    key_warnings = []

    for drug in drug_data:
        full_text = (drug["warnings"] or "") + " " + (drug["boxed_warning"] or "")
        warning = extract_key_warning(
            full_text,
            bleeding_keywords + heart_keywords + organ_keywords + danger_keywords
        )

        if warning:
            key_warnings.append(f"{drug['name'].capitalize()}: {warning}")
    
    if overlap_danger or (overlap_bleeding and overlap_heart):
        severity = "danger"
        summary = (
            f"Taking {' and '.join([d['name'] for d in drug_data])} together is considered high risk.\n\n"
            f"{(chr(10)+chr(10)).join(key_warnings[:2]) if key_warnings else ''}\n\n"
            f"Do not combine these medications without direct supervision from your doctor."
        )
    
    elif overlap_bleeding or overlap_heart or overlap_organ:
        severity = "caution"
        summary = (
            f"Use caution when taking {' and '.join([d['name'] for d in drug_data])} together.\n\n"
            f"{key_warnings[0] if key_warnings else ''}\n\n"
            f"Consult your doctor or phamacist before combining these medications."
        )
    
    else:
        severity = "safe"
        summary = (
            f"No major interactions detected between "
            f"{' and '.join([d['name'] for d in drug_data])}.\n\n"
            f"Always consult your healthcare provider if you have any concerns."
        )
    
    return {
        "severity": severity,
        "summary": summary,
        "flags": flags,
        "drugs_analyzed": [d["name"] for d in drug_data]
    }

@app.get("/interact")

def check_interactions(drugs: List[str] = Query(...)):
    drug_data = []

    for drug in drugs:
        data = fetch_drug_data(drug)

        if data is None:
            return {"error": f"Could not find drug: {drug}"}
        
        drug_data.append(data)
    
    analysis = analyze_interactions(drug_data)

    return {
        "analysis": analysis,
        "drugs": drug_data
    }