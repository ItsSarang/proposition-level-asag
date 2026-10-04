"""Script to inspect and verify dataset availability in data/raw/mohler_asag/."""
import os
import sys

def verify_dataset():
    data_dir = "data/raw/mohler_asag"
    if not os.path.exists(data_dir):
        print(f"Error: Dataset directory '{data_dir}' not found.")
        print("Please place the raw Mohler ASAG dataset in 'data/raw/mohler_asag/'.")
        sys.exit(1)
    
    files = os.listdir(data_dir)
    print(f"Dataset verified: {len(files)} items found in '{data_dir}'.")
    return True

if __name__ == "__main__":
    verify_dataset()
