"""
V0 Model Predictor Adapter (TF-IDF + Cosine Baseline).

Provides the unified evaluation adapter for the lexical comparison baseline.
Calculates unigram word-level TF-IDF cosine similarity between the reference
answer and the student answer.
"""
from typing import Any, Dict, Optional
from baseline.tfidf_cosine.baseline import TfidfCosineBaseline
from common.types import GradingResult


class V0Predictor:
    """
    Evaluation adapter for Model V0: TF-IDF Cosine Baseline.

    Evaluates answers strictly by lexical vector overlap, serving as the
    lower-complexity baseline against which structural and semantic ASAG
    extensions are benchmarked.
    """

    def __init__(self, scale: float = 5.0, lowercase: bool = True, **kwargs: Any) -> None:
        """
        Initialize V0Predictor with scale and text normalization options.

        Parameters
        ----------
        scale : float, default=5.0
            Maximum point scale for scaled grades.
        lowercase : bool, default=True
            Whether to convert tokens to lowercase before vectorization.
        """
        self.scale = float(scale)
        self.model = TfidfCosineBaseline(lowercase=lowercase)

    def evaluate(self, question: str, reference_answer: str, student_answer: str) -> GradingResult:
        """
        Evaluate a student answer against the reference using TF-IDF cosine similarity.

        Parameters
        ----------
        question : str
            The prompt question (unused in bag-of-words similarity, retained for interface conformity).
        reference_answer : str
            The instructor reference answer.
        student_answer : str
            The student response.

        Returns
        -------
        GradingResult
            Standardized grading result containing normalized score and scaled grade.
        """
        sim = float(self.model.similarity(reference_answer, student_answer))
        grade = float(round(sim * self.scale, 4))
        return GradingResult(
            model_version="V0",
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            normalized_score=sim,
            grade=grade,
            max_points=self.scale,
            explanation=f"TF-IDF cosine similarity: {sim:.4f}",
            metadata={"cosine_similarity": sim},
        )
