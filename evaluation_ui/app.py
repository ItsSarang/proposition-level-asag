"""
Flask Application for the ASAG Evaluation Lab (Phase 2).

A clean, research-oriented evaluation and demonstration interface for comparing:
- V0: TF-IDF Baseline
- V1: Base ASAG
- V2: Historical Proposed ASAG
- V3: Current / Overhauled Proposed ASAG

Research Safety:
- Thin presentation layer over existing evaluation services.
- Never fabricates scores or metrics.
- All evaluation logic remains in baseline/, base_asag/, and proposed_asag/.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional
from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from evaluation_ui.services.comparison import ASAGComparisonService
from evaluation_ui.services.evaluator import ASAGEvaluatorService

# Global in-memory storage for interactive sessions (no database)
EVALUATION_CACHE: Dict[str, Any] = {}
EXPERIMENT_CACHE: Dict[str, Any] = {}

# Standard demonstration examples from research documentation
PRESET_EXAMPLES = {
    "primary_key": {
        "title": "Primary Key Purpose (GEMINI.md Motivation)",
        "question": "What is the purpose of a primary key?",
        "reference_answer": "A primary key uniquely identifies each record in a table.",
        "student_answers": [
            "A primary key uniquely identifies every row in a table.",
            "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
            "A primary key uniquely identifies each record in a table and can contain duplicate values.",
            "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.",
        ],
    },
    "bst": {
        "title": "Binary Search Tree (Mohler Q8.1)",
        "question": "What is a binary search tree?",
        "reference_answer": "A binary search tree is a binary tree where the left child of a node has a key less than the parent and the right child has a key greater than the parent.",
        "student_answers": [
            "A tree where nodes to the left are smaller and nodes to the right are greater than the root.",
            "A binary tree where left is smaller and right is greater. An AVL tree is a balanced binary search tree.",
            "A tree where every node can have any number of children greater than two.",
        ],
    },
}


def create_app(test_config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    app.config["SECRET_KEY"] = "asag-evaluation-lab-research-key"
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

    if test_config:
        app.config.update(test_config)

    evaluator_service = ASAGEvaluatorService()
    comparison_service = ASAGComparisonService(evaluator_service=evaluator_service)

    @app.route("/", methods=["GET"])
    def index():
        """Main page: Multi-student quick comparison input."""
        preset_key = request.args.get("preset", "primary_key")
        preset = PRESET_EXAMPLES.get(preset_key, PRESET_EXAMPLES["primary_key"])
        return render_template(
            "index.html",
            preset=preset,
            preset_key=preset_key,
            all_presets=PRESET_EXAMPLES,
        )

    @app.route("/evaluate", methods=["POST"])
    def evaluate():
        """Evaluate submitted question, reference, and student answers."""
        question = request.form.get("question", "").strip()
        reference_answer = request.form.get("reference_answer", "").strip()
        raw_answers = request.form.getlist("student_answers")

        # Clean and filter non-empty student answers
        student_answers = [a.strip() for a in raw_answers if a and a.strip()]

        if not question or not reference_answer or not student_answers:
            return render_template(
                "index.html",
                error="Please provide a Question, Reference Answer, and at least one Student Answer.",
                preset={
                    "question": question,
                    "reference_answer": reference_answer,
                    "student_answers": student_answers or [""],
                },
                all_presets=PRESET_EXAMPLES,
            )

        # Execute evaluation
        eval_id = str(uuid.uuid4())
        results = evaluator_service.evaluate_batch(
            question=question,
            reference_answer=reference_answer,
            student_answers=student_answers,
        )

        EVALUATION_CACHE[eval_id] = {
            "eval_id": eval_id,
            "question": question,
            "reference_answer": reference_answer,
            "results": results,
            "student_count": len(results),
        }

        return render_template(
            "results.html",
            eval_id=eval_id,
            question=question,
            reference_answer=reference_answer,
            results=results,
        )

    @app.route("/result/<eval_id>/<int:answer_index>", methods=["GET"])
    def result_detail(eval_id: str, answer_index: int):
        """Detailed view for a specific evaluated answer."""
        eval_data = EVALUATION_CACHE.get(eval_id)
        if not eval_data:
            return redirect(url_for("index"))

        results = eval_data.get("results", [])
        if answer_index < 0 or answer_index >= len(results):
            abort(404, description="Student answer index out of range.")

        detail = results[answer_index]
        return render_template(
            "detail.html",
            eval_id=eval_id,
            answer_index=answer_index,
            detail=detail,
            question=eval_data["question"],
            reference_answer=eval_data["reference_answer"],
            total_answers=len(results),
        )

    @app.route("/experiment", methods=["GET"])
    def experiment():
        """Batch experiment mode page."""
        exp_id = request.args.get("exp_id")
        sort_by = request.args.get("sort_by", "absolute_error")
        experiment_data = None
        if exp_id and exp_id in EXPERIMENT_CACHE:
            raw_exp = EXPERIMENT_CACHE[exp_id]
            sorted_recs = comparison_service.sort_error_records(
                records=raw_exp["batch_result"]["records"],
                sort_by=sort_by,
            )
            experiment_data = {
                "exp_id": exp_id,
                "batch_result": raw_exp["batch_result"],
                "records": sorted_recs,
                "sort_by": sort_by,
            }

        return render_template(
            "experiment.html",
            experiment_data=experiment_data,
        )

    @app.route("/experiment/upload", methods=["POST"])
    def experiment_upload():
        """Handle CSV file upload for batch experiment."""
        if "csv_file" not in request.files:
            return render_template("experiment.html", error="No file part in upload request.")

        file = request.files["csv_file"]
        if not file or file.filename == "":
            return render_template("experiment.html", error="No file selected.")

        try:
            content = file.read().decode("utf-8")
        except UnicodeDecodeError:
            file.seek(0)
            content = file.read().decode("latin-1")

        max_limit = request.form.get("max_records")
        limit_val = int(max_limit) if max_limit and max_limit.isdigit() else None

        batch_result = comparison_service.process_csv_batch(content, max_records=limit_val)

        exp_id = str(uuid.uuid4())
        EXPERIMENT_CACHE[exp_id] = {
            "exp_id": exp_id,
            "filename": file.filename,
            "batch_result": batch_result,
        }

        return redirect(url_for("experiment", exp_id=exp_id))

    @app.route("/experiment/download/<exp_id>", methods=["GET"])
    def experiment_download(exp_id: str):
        """Download generated predictions as CSV."""
        exp_data = EXPERIMENT_CACHE.get(exp_id)
        if not exp_data:
            abort(404, description="Experiment ID not found.")

        csv_text = comparison_service.generate_predictions_csv(exp_data["batch_result"])
        return Response(
            csv_text,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=asag_predictions_{exp_id[:8]}.csv"},
        )

    @app.route("/validation", methods=["GET"])
    def validation():
        """Future human validation placeholder page (Phase 10)."""
        return render_template("validation.html")

    @app.route("/documentation", methods=["GET"])
    def documentation():
        """Research documentation and engine reference."""
        return render_template("documentation.html")

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
