"""CLI to execute any ASAG model version (V0-V5) on an arbitrary short answer."""
import argparse
import sys
import json
from models.registry import get_model, list_models

def main():
    parser = argparse.ArgumentParser(description="Run ASAG Grading Model (V0-V5)")
    parser.add_argument("--model", type=str, default="V5", help="Model version: V0, V1, V2, V3, V4, V5")
    parser.add_argument("--question", type=str, default="What is the purpose of a primary key?")
    parser.add_argument("--reference", type=str, default="A primary key uniquely identifies each record in a table.")
    parser.add_argument("--student", type=str, default="A primary key uniquely identifies each record in a table and cannot contain NULL values.")
    parser.add_argument("--scale", type=float, default=5.0)
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    
    args = parser.parse_args()
    
    try:
        model = get_model(args.model, scale=args.scale)
    except ValueError as e:
        print(f"Error: {e}")
        print("Available models:")
        for m in list_models():
            print(f"  {m['version']}: {m['name']} ({m['status']})")
        sys.exit(1)
        
    result = model.evaluate(args.question, args.reference, args.student)
    
    if args.json:
        res_dict = {
            "model_version": result.model_version,
            "question": result.question,
            "reference_answer": result.reference_answer,
            "student_answer": result.student_answer,
            "normalized_score": result.normalized_score,
            "grade": result.grade,
            "max_points": result.max_points,
            "explanation": result.explanation,
        }
        print(json.dumps(res_dict, indent=2))
    else:
        print(f"=== Grading Result ({result.model_version}) ===")
        print(f"Question:         {result.question}")
        print(f"Reference Answer: {result.reference_answer}")
        print(f"Student Answer:   {result.student_answer}")
        print(f"Normalized Score: {result.normalized_score:.4f}")
        print(f"Final Grade:      {result.grade:.4f} / {result.max_points}")
        print(f"Explanation:      {result.explanation}")

if __name__ == "__main__":
    main()
