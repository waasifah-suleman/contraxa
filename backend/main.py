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

# TODO: prescription drugs like warfarin use different OpenFDA fields
# need to add fallback to fetch from warnings_and_cautions if purpose and active_ingredients come back Unknown

def fetch_drug_data(drug_name: str):
    url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug_name}&limit=1"

    response = requests.get(url)

    if response.status_code != 200:
        return None
    
    data = response.json()

    if not data.get("results"):
        return None
    
    result = data["results"][0]

    return {
        "name": drug_name,
        "purpose": result.get("purpose", ["Unknown"])[0],
        "active_ingredients": result.get("active_ingredient", ["Unknown"])[0],
        "warnings": result.get("warnings", ["None available"])[0],
        "boxed_warning": result.get("boxed_warning", [None])[0],
        "side_effects": result.get("adverse_reactions", ["None listed"])[0]
    }


def analyze_interactions(drug_data: list):
    bleeding_keywords = [
        "bleeding", "blood thinning", "anticoagulant", "hemorrhage",
        "blood thinner", "warfarin", "aspirin", "nsaid", "bruising"
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

    flags = []

    all_warnings_text = ""

    for drug in drug_data:
        if drug["warnings"]:
            all_warnings_text += drug["warnings"].lower() + " "
        if drug["boxed_warning"]:
            all_warnings_text += drug["boxed_warning"].lower() + " "
    
    bleeding_hits = [kw for kw in bleeding_keywords if kw in all_warnings_text]
    heart_hits = [kw for kw in heart_keywords if kw in all_warnings_text]
    organ_hits = [kw for kw in organ_keywords if kw in all_warnings_text]
    danger_hits = [kw for kw in danger_keywords if kw in all_warnings_text]

    if bleeding_hits:
        flags.append("bleeding risk detected")
    if heart_hits:
        flags.append("cardiovascular risk detected")
    if organ_hits:
        flags.append("liver or kidney stress detected")

    def extract_key_warning(text: str, keywords: list):
        sentences = text.split(".")

        for sentence in sentences:
            sentence = sentence.strip()

            if any(kw in sentence.lower() for kw in keywords):
                if 20 < len(sentence) > 300:
                    return sentence + "."
        
        return None
    
    key_warnings = []
    for drug in drug_data:
        full_text = (drug["warnings"] or "") + " " + (drug["boxed_warning"] or "")

        warning = extract_key_warning(full_text, 
            bleeding_keywords + heart_keywords + organ_keywords + danger_keywords)
        
        if warning:
            key_warnings.append(f"{drug['name'].capitalize()}: {warning}")
    
    if danger_hits or (bleeding_hits and heart_hits):
        severity = "danger"
        summary = (
            f"Taking {' and '.join([d['name'] for d in drug_data])} together is considered high risk. "
            f"{' '.join(key_warnings[:2]) if key_warnings else ''} "
            f"Do not combine these medications without direct supervision from your doctor."
        )
        
    elif bleeding_hits or heart_hits or organ_hits:
        severity = "caution"
        summary = (
            f"Use caution when taking {' and '.join([d['name'] for d in drug_data])} together. "
            f"{key_warnings[0] if  key_warnings else ''}"
            f"Consult your doctor or pharmacist before combining these medications."
        )
    
    else:
        severity = "safe"
        summary = (
            f"No major interactions detected between "
            f"{' and '.join(d['name'] for d in drug_data)}. "
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