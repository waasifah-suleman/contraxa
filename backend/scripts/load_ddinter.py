import sys
import os
import csv
import glob

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from database import Base, engine, SessionLocal
from models import DrugInteraction

RAW_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data", "ddinter_raw")


def normalize_pair(drug_a: str, drug_b: str):
    a = drug_a.strip().lower()
    b = drug_b.strip().lower()
    return tuple(sorted([a, b]))

def load_all_files():

    db = SessionLocal()

    print("Clearing any existing drug_interactions data...")
    db.query(DrugInteraction).delete()

    db.commit()

    seen_pairs = set()

    csv_files = glob.glob(os.path.join(RAW_DATA_FOLDER, "*.csv"))

    print(f"Found {len(csv_files)} CSV files to process.")

    total_inserted = 0

    for file_path in csv_files:

        print(f"Processing {os.path.basename(file_path)}...")

        batch = []

        with open(file_path, newline="", encoding="utf-8") as csv_file:

            reader = csv.DictReader(csv_file)

            for row in reader:

                drug_a_raw = row.get("Drug_A")
                drug_b_raw = row.get("Drug_B")
                severity = row.get("Level")

                if not drug_a_raw or not drug_b_raw or not severity:

                    continue

                drug_a, drug_b = normalize_pair(drug_a_raw, drug_b_raw)

                pair_key = (drug_a, drug_b)

                if pair_key in seen_pairs:

                    continue

                seen_pairs.add(pair_key)

                batch.append(
                    DrugInteraction(
                        drug_a=drug_a,
                        drug_b=drug_b,
                        severity=severity.strip()
                    )
                )

        db.bulk_save_objects(batch)

        db.commit()

        total_inserted += len(batch)
        print(f"  -> Inserted {len(batch)} unique pairs from this file.")

    db.close()

    print(f"\nDone. {total_inserted} total drug interaction pairs loaded.")


if __name__ == "__main__":

    print("Creating database tables if they don't already exist...")
    Base.metadata.create_all(bind=engine)


    load_all_files()