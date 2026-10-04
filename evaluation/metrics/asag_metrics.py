"""ASAG Evaluation Metrics Module (Stage 15.2).

Provides standard, transparent implementations of evaluation metrics for
Automated Short Answer Grading:
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Pearson correlation coefficient (r)
- Spearman rank correlation coefficient (rho)
- Quadratic Weighted Kappa (QWK)

Design Principles:
------------------
- Independent of specific ASAG models.
- Operates on 1D sequences of numeric scores (e.g. human score_ave vs model grades).
- Handles edge cases robustly (e.g., constant predictions, zero variance, NaN).
- Preserves explicit sample counts and p-values where applicable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import cohen_kappa_score


def normalize_to_grade(normalized_score: float, max_points: float = 5.0) -> float:
    """Convert an internal normalized score in [0.0, 1.0] to the target grade scale [0.0, max_points].

    Parameters
    ----------
    normalized_score : float
        Score in range [0.0, 1.0].
    max_points : float, default=5.0
        Target maximum grade (e.g., 5.0 for Mohler dataset).

    Returns
    -------
    float
        Scaled grade rounded to 4 decimal places.
    """
    if normalized_score is None:
        raise ValueError("normalized_score cannot be None.")
    return float(round(float(normalized_score) * max_points, 4))


def validate_metric_inputs(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> Tuple[np.ndarray, np.ndarray]:
    """Validate that y_true and y_pred are non-empty 1D numeric arrays of equal length.

    Raises
    ------
    ValueError
        If inputs are empty, have unequal lengths, or contain NaNs/infs.
    """
    if y_true is None or y_pred is None:
        raise ValueError("y_true and y_pred cannot be None.")

    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    if y_t.ndim != 1 or y_p.ndim != 1:
        raise ValueError(f"Inputs must be 1-dimensional, got y_true: {y_t.ndim}D, y_pred: {y_p.ndim}D.")

    if len(y_t) == 0:
        raise ValueError("Inputs cannot be empty.")

    if len(y_t) != len(y_p):
        raise ValueError(
            f"Length mismatch: y_true has {len(y_t)} samples, y_pred has {len(y_p)} samples."
        )

    if np.any(np.isnan(y_t)) or np.any(np.isnan(y_p)):
        raise ValueError("Inputs contain NaN values.")

    if np.any(np.isinf(y_t)) or np.any(np.isinf(y_p)):
        raise ValueError("Inputs contain infinite values.")

    return y_t, y_p


def mean_absolute_error(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute Mean Absolute Error (MAE)."""
    y_t, y_p = validate_metric_inputs(y_true, y_pred)
    return float(np.mean(np.abs(y_t - y_p)))


def root_mean_squared_error(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute Root Mean Squared Error (RMSE)."""
    y_t, y_p = validate_metric_inputs(y_true, y_pred)
    return float(np.sqrt(np.mean((y_t - y_p) ** 2)))


def pearson_correlation(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> Tuple[Optional[float], Optional[float]]:
    """Compute Pearson correlation coefficient (r) and its two-tailed p-value.

    Returns (None, None) if either array has zero variance (constant values)
    or sample size is less than 2.
    """
    y_t, y_p = validate_metric_inputs(y_true, y_pred)
    if len(y_t) < 2:
        return None, None

    std_t = np.std(y_t)
    std_p = np.std(y_p)

    if std_t < 1e-12 or std_p < 1e-12:
        # Constant predictions or constant ground truth
        return None, None

    r_val, p_val = pearsonr(y_t, y_p)
    return float(r_val), float(p_val)


def spearman_correlation(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> Tuple[Optional[float], Optional[float]]:
    """Compute Spearman rank correlation coefficient (rho) and its two-tailed p-value.

    Returns (None, None) if either array has zero variance or sample size < 2.
    """
    y_t, y_p = validate_metric_inputs(y_true, y_pred)
    if len(y_t) < 2:
        return None, None

    std_t = np.std(y_t)
    std_p = np.std(y_p)

    if std_t < 1e-12 or std_p < 1e-12:
        return None, None

    res = spearmanr(y_t, y_p)
    return float(res.statistic), float(res.pvalue)


def quadratic_weighted_kappa(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    min_rating: int = 0,
    max_rating: int = 5,
    round_mode: str = "nearest_integer",
) -> Optional[float]:
    """Compute Quadratic Weighted Kappa (QWK) between true and predicted ratings.

    Note on Continuous ASAG Predictions:
    ASAG systems produce continuous numerical scores (e.g. 3.42 / 5.0).
    Cohen's Quadratic Weighted Kappa operates on discrete ordinal rating categories.
    Following standard ASAG evaluation conventions, predictions are rounded to
    the nearest discrete rating level and clipped to [min_rating, max_rating].

    Parameters
    ----------
    y_true : Sequence[float]
        Ground truth ratings (e.g., integer or rounded half-points).
    y_pred : Sequence[float]
        Predicted ratings from an ASAG system.
    min_rating : int, default=0
        Minimum valid rating level on the scale.
    max_rating : int, default=5
        Maximum valid rating level on the scale.
    round_mode : str, default='nearest_integer'
        Rounding strategy: 'nearest_integer' rounds to integer levels [0..5];
        'half_integer' rounds to increments of 0.5 mapped to integers [0..10].

    Returns
    -------
    Optional[float]
        QWK score in range [-1.0, 1.0], or 0.0 if all predictions are identical.
    """
    y_t, y_p = validate_metric_inputs(y_true, y_pred)

    if round_mode == "nearest_integer":
        labels = list(range(min_rating, max_rating + 1))
        # Round true and predicted to nearest integer and clip
        t_disc = np.clip(np.round(y_t).astype(int), min_rating, max_rating)
        p_disc = np.clip(np.round(y_p).astype(int), min_rating, max_rating)
    elif round_mode == "half_integer":
        # 11 levels: 0.0, 0.5, ..., 5.0 -> mapped to integer scale 0..10
        min_level = min_rating * 2
        max_level = max_rating * 2
        labels = list(range(min_level, max_level + 1))
        t_disc = np.clip(np.round(y_t * 2.0).astype(int), min_level, max_level)
        p_disc = np.clip(np.round(y_p * 2.0).astype(int), min_level, max_level)
    else:
        raise ValueError(f"Unknown round_mode: {round_mode}. Use 'nearest_integer' or 'half_integer'.")

    # If predictions have zero variation, cohen_kappa_score returns 0.0
    if len(np.unique(p_disc)) <= 1 and len(np.unique(t_disc)) <= 1:
        # Trivial case: all predictions and all truths are identical
        return 1.0 if p_disc[0] == t_disc[0] else 0.0

    try:
        score = cohen_kappa_score(t_disc, p_disc, labels=labels, weights="quadratic")
        if math.isnan(score):
            return 0.0
        return float(score)
    except Exception:
        return 0.0


@dataclass(frozen=True)
class EvaluationMetrics:
    """Container for comprehensive evaluation metrics of an ASAG system."""

    system_name: str
    n_samples: int
    mae: float
    rmse: float
    pearson_r: Optional[float]
    pearson_p: Optional[float]
    spearman_rho: Optional[float]
    spearman_p: Optional[float]
    qwk: Optional[float]
    ground_truth_mean: float
    ground_truth_std: float
    predicted_mean: float
    predicted_std: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)


def compute_all_metrics(
    system_name: str,
    y_true: Sequence[float],
    y_pred: Sequence[float],
    min_rating: int = 0,
    max_rating: int = 5,
) -> EvaluationMetrics:
    """Compute all standard evaluation metrics for an ASAG prediction set against ground truth."""
    y_t, y_p = validate_metric_inputs(y_true, y_pred)

    mae_val = mean_absolute_error(y_t, y_p)
    rmse_val = root_mean_squared_error(y_t, y_p)
    p_r, p_p = pearson_correlation(y_t, y_p)
    s_rho, s_p = spearman_correlation(y_t, y_p)
    qwk_val = quadratic_weighted_kappa(
        y_t, y_p, min_rating=min_rating, max_rating=max_rating
    )

    return EvaluationMetrics(
        system_name=system_name,
        n_samples=len(y_t),
        mae=float(round(mae_val, 4)),
        rmse=float(round(rmse_val, 4)),
        pearson_r=float(round(p_r, 4)) if p_r is not None else None,
        pearson_p=float(round(p_p, 6)) if p_p is not None else None,
        spearman_rho=float(round(s_rho, 4)) if s_rho is not None else None,
        spearman_p=float(round(s_p, 6)) if s_p is not None else None,
        qwk=float(round(qwk_val, 4)) if qwk_val is not None else None,
        ground_truth_mean=float(round(float(np.mean(y_t)), 4)),
        ground_truth_std=float(round(float(np.std(y_t)), 4)),
        predicted_mean=float(round(float(np.mean(y_p)), 4)),
        predicted_std=float(round(float(np.std(y_p)), 4)),
    )
