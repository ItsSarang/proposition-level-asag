"""Evaluation runner for Model V3 (Enhanced Proposition-Level ASAG)."""
from models.registry import get_model
from common.types import GradingResult

def evaluate_single(
    question: str,
    reference_answer: str,
    student_answer: str,
    scale: float = 5.0,
) -> GradingResult:
    """
    Evaluate a single question-answer pair using Model V3 (Enhanced Proposition ASAG).

    Parameters
    ----------
    question : str
        Question prompt text.
    reference_answer : str
        Instructor ground-truth reference answer.
    student_answer : str
        Student response text.
    scale : float, default=5.0
        Grading scale maximum.

    Returns
    -------
    GradingResult
        Unified grading result with Hungarian bipartite matching and bounded score.
    """
    model = get_model("V3", scale=scale)
    return model.evaluate(question, reference_answer, student_answer)

if __name__ == "__main__":
    import sys
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    s = "A primary key uniquely identifies each record in a table." if len(sys.argv) <= 1 else sys.argv[1]
    res = evaluate_single(q, r, s)
    print(f"V3 Grade: {res.grade:.4f}/{res.max_points} ({res.explanation})")
