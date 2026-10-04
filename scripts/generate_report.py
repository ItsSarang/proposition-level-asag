"""Script to print or export comprehensive benchmark results across all model versions V0-V5."""
import json
import os

def generate_comparison_table():
    versions = ["v0", "v1", "v2", "v3", "v4", "v5"]
    print("=========================================================================================")
    print("                     PROPOSITION-LEVEL ASAG BENCHMARK COMPARISON                         ")
    print("=========================================================================================")
    print(f"{'Version':<10} | {'Model Name':<32} | {'Pearson r':<10} | {'Spearman rho':<12} | {'MAE':<8} | {'RMSE':<8}")
    print("-" * 89)
    for v in versions:
        path = f"experiments/frozen/{v}/summary.json"
        if os.path.exists(path):
            with open(path) as f:
                d = json.load(f)
                name = d.get("name", v)
                met = d.get("metrics", {})
                pr = f"{met.get('pearson_r', 0.0):.4f}" if "pearson_r" in met else "N/A"
                sr = f"{met.get('spearman_rho', 0.0):.4f}" if "spearman_rho" in met else "N/A"
                mae = f"{met.get('mae', 0.0):.4f}" if "mae" in met else "N/A"
                rmse = f"{met.get('rmse', 0.0):.4f}" if "rmse" in met else "N/A"
                print(f"{v.upper():<10} | {name:<32} | {pr:<10} | {sr:<12} | {mae:<8} | {rmse:<8}")
    print("=========================================================================================")

if __name__ == "__main__":
    generate_comparison_table()
