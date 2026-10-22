"""
Flask Application for Proposition-Level ASAG Backend.

Entry point for ASAG Backend serving:
- POST /api/analyze: 7-phase deep proposition inspection for ASAG Lab Workbench
- POST /api/grade: Scoring across models V0-V5
- GET /api/models: List available ASAG model versions
- GET /api/health: Health check endpoint
"""

import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure project root is in python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.services.analysis_service import ASAGAnalysisService
from backend.services.grading_service import GradingService
from backend.services.model_registry import BackendModelRegistry

app = Flask(__name__)

# Enable CORS across all routes for React/Vite development server
CORS(app, resources={r"/*": {"origins": "*"}})

# Lazy-loaded services
_analysis_service = None
_grading_service = None


def get_analysis_service() -> ASAGAnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = ASAGAnalysisService()
    return _analysis_service


def get_grading_service() -> GradingService:
    global _grading_service
    if _grading_service is None:
        _grading_service = GradingService()
    return _grading_service


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "name": "ASAG Lab Flask API",
        "description": "Proposition-Level Automated Short Answer Grading Engine",
        "version": "1.0.0",
        "framework": "Flask",
        "endpoints": {
            "health": "/api/health",
            "models": "/api/models",
            "analyze": "POST /api/analyze",
            "grade": "POST /api/grade",
        },
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "framework": "Flask",
        "service": "asag-backend",
        "models_available": ["V0", "V1", "V5"],
    })


@app.route("/api/models", methods=["GET"])
def list_models():
    models = BackendModelRegistry.list_models()
    return jsonify({
        "models": models,
        "default": "V5",
    })


@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def analyze_endpoint():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(force=True, silent=True) or {}
    question = data.get("question", "").strip()
    reference_answer = data.get("reference_answer", "").strip()
    student_answer = data.get("student_answer", "").strip()
    scale = float(data.get("scale", 5.0))

    if not question:
        return jsonify({"detail": "question field is required."}), 400
    if not reference_answer:
        return jsonify({"detail": "reference_answer field is required."}), 400
    if not student_answer:
        return jsonify({"detail": "student_answer field is required."}), 400

    try:
        service = get_analysis_service()
        result = service.analyze(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            scale=scale,
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 400
    except Exception as e:
        return jsonify({"detail": f"Analysis engine error: {str(e)}"}), 500


@app.route("/api/grade", methods=["POST", "OPTIONS"])
def grade_endpoint():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(force=True, silent=True) or {}
    question = data.get("question", "").strip()
    reference_answer = data.get("reference_answer", "").strip()
    student_answer = data.get("student_answer", "").strip()
    model = data.get("model", "V5").strip().upper()
    scale = float(data.get("scale", 5.0))

    if not question or not reference_answer or not student_answer:
        return jsonify({"detail": "question, reference_answer, and student_answer are required."}), 400

    try:
        service = get_grading_service()
        result = service.grade(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            model_id=model,
            scale=scale,
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"detail": str(e)}), 400
    except Exception as e:
        return jsonify({"detail": f"Grading error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 60)
    print(f"Starting ASAG Lab Flask API Server on http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/api/health")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=True)
