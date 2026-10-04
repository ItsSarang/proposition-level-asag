"""Script to verify and preprocess raw Mohler records into processed CSV files."""
import os
import sys

def run_preprocessing():
    from evaluation.dataset.mohler_loader import MohlerLoader
    loader = MohlerLoader()
    dataset = loader.load()
    print(f"Preprocessing verified: Loaded {len(dataset.active_records)} active records out of {len(dataset.all_records)} total records.")
    
    os.makedirs("data/processed", exist_ok=True)
    out_active = "data/processed/mohler_active_records.csv"
    if not os.path.exists(out_active):
        dataset.export_active_to_csv(out_active)
        print(f"Exported active records to {out_active}")
    else:
        print(f"Existing active records file found at {out_active}")

if __name__ == "__main__":
    run_preprocessing()
