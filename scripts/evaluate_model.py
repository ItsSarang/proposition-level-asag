"""CLI to evaluate a model version (V0-V5) against sample or full benchmark records."""
import argparse
import sys
from models.registry import get_model, list_models
from evaluation.dataset.mohler_loader import MohlerLoader
from evaluation.metrics.asag_metrics import compute_asag_metrics

def main():
    parser = argparse.ArgumentParser(description="Evaluate ASAG Model on Benchmark Records")
    parser.add_argument("--model", type=str, default="V5", help="Model version: V0, V1, V2, V3, V4, V5")
    parser.add_argument("--limit", type=int, default=5, help="Number of records to evaluate (default 5 for quick check)")
    parser.add_argument("--scale", type=float, default=5.0)
    args = parser.parse_args()
    
    loader = MohlerLoader()
    dataset = loader.load()
    records = dataset.active_records[:args.limit] if args.limit > 0 else dataset.active_records
    
    model = get_model(args.model, scale=args.scale)
    
    y_true = []
    y_pred = []
    print(f"Evaluating {args.model} on {len(records)} records...")
    for idx, rec in enumerate(records):
        res = model.evaluate(rec.question_text, rec.reference_answer, rec.student_answer)
        y_true.append(rec.human_score_avg)
        y_pred.append(res.grade)
        if idx < 3:
            print(f"[{idx+1}] Human={rec.human_score_avg:.2f}, Pred={res.grade:.2f} ({res.explanation[:40]}...)")
            
    if len(y_true) >= 5:
        metrics = compute_asag_metrics(y_true, y_pred, max_points=args.scale)
        print(f"\nMetrics summary on {len(records)} records:")
        print(f"  MAE:          {metrics.mae:.4f}")
        print(f"  RMSE:         {metrics.rmse:.4f}")
        print(f"  Pearson r:    {metrics.pearson_r:.4f}")
        print(f"  Spearman rho: {metrics.spearman_rho:.4f}")

if __name__ == "__main__":
    main()
