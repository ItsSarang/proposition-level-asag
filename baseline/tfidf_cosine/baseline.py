"""
TF-IDF + Cosine Similarity Baseline for Short Answer Grading.

This module provides a classical, surface-level lexical similarity baseline
using term frequency-inverse document frequency (TF-IDF) representation
and cosine similarity comparison.
"""

from typing import Tuple, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TfidfCosineBaseline:
    """
    A simple baseline model that computes the cosine similarity between
    TF-IDF vectors of a reference answer and a student answer.
    """

    def __init__(self, lowercase: bool = True, token_pattern: str = r"(?u)\b\w+\b"):
        r"""
        Initialize the TF-IDF vectorizer configuration.

        Parameters
        ----------
        lowercase : bool, default=True
            Whether to convert characters to lowercase before tokenization.
        token_pattern : str, default=r"(?u)\b\w+\b"
            Regular expression denoting what constitutes a "token".
        """
        self.lowercase = lowercase
        self.token_pattern = token_pattern

    def validate_inputs(self, reference_answer: str, student_answer: str) -> Tuple[str, str]:
        """
        Validate and sanitize string inputs.

        Parameters
        ----------
        reference_answer : str
            The ground truth reference answer.
        student_answer : str
            The student's submitted answer.

        Returns
        -------
        Tuple[str, str]
            Sanitized (stripped) reference and student answers.

        Raises
        ------
        TypeError
            If either input is not a string.
        ValueError
            If either input is empty or consists solely of whitespace.
        """
        if not isinstance(reference_answer, str):
            raise TypeError(
                f"reference_answer must be a string, got {type(reference_answer).__name__}."
            )
        if not isinstance(student_answer, str):
            raise TypeError(
                f"student_answer must be a string, got {type(student_answer).__name__}."
            )

        ref_clean = reference_answer.strip()
        stu_clean = student_answer.strip()

        if not ref_clean:
            raise ValueError("reference_answer cannot be empty or contain only whitespace.")
        if not stu_clean:
            raise ValueError("student_answer cannot be empty or contain only whitespace.")

        return ref_clean, stu_clean

    def similarity(self, reference_answer: str, student_answer: str) -> float:
        """
        Compute the cosine similarity between the TF-IDF representations of
        the reference answer and the student answer.

        Parameters
        ----------
        reference_answer : str
            The reference answer against which the student is evaluated.
        student_answer : str
            The student response.

        Returns
        -------
        float
            Cosine similarity score bounded in [0.0, 1.0].
        """
        ref_clean, stu_clean = self.validate_inputs(reference_answer, student_answer)

        vectorizer = TfidfVectorizer(
            lowercase=self.lowercase,
            token_pattern=self.token_pattern
        )

        try:
            tfidf_matrix = vectorizer.fit_transform([ref_clean, stu_clean])
        except ValueError:
            # Occurs when inputs contain no extractable tokens (e.g. pure punctuation)
            return 0.0

        # Calculate cosine similarity between document 0 (ref) and document 1 (stu)
        score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])

        # Clamp floating-point imprecision to [0.0, 1.0]
        score = max(0.0, min(1.0, score))
        return float(round(score, 6))


def compute_tfidf_cosine_similarity(
    reference_answer: str,
    student_answer: str,
    lowercase: bool = True
) -> float:
    """
    Convenience function to calculate the TF-IDF cosine similarity between two answers.

    Parameters
    ----------
    reference_answer : str
        The reference answer text.
    student_answer : str
        The student answer text.
    lowercase : bool, default=True
        Whether to convert characters to lowercase before vectorizing.

    Returns
    -------
    float
        Cosine similarity score bounded in [0.0, 1.0].
    """
    baseline = TfidfCosineBaseline(lowercase=lowercase)
    return baseline.similarity(reference_answer, student_answer)
