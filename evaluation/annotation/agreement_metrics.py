"""
Annotation Agreement and Classification Evaluation Metrics (Phase 10).

Calculates inter-annotator agreement (Raw Agreement, Cohen's Kappa) and
classification performance (per-class Precision, Recall, F1, Macro-F1, Confusion Matrix)
for human annotation studies.

Enforces strict research integrity: when human labels are not yet provided,
clearly reports status as PENDING_HUMAN_ANNOTATIONS without fabricating results.
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


VALID_LABELS = {
    "CORRECT_ADDITIONAL",
    "IRRELEVANT",
    "INCORRECT",
    "UNCERTAIN",
}


@dataclass(frozen=True)
class InterAnnotatorAgreementResult:
    """Inter-annotator reliability metrics."""
    total_items: int
    agreed_items: int
    raw_agreement: float
    cohens_kappa: float
    label_distribution_1: Dict[str, int]
    label_distribution_2: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_items": self.total_items,
            "agreed_items": self.agreed_items,
            "raw_agreement": round(self.raw_agreement, 4),
            "cohens_kappa": round(self.cohens_kappa, 4),
            "label_distribution_annotator_1": self.label_distribution_1,
            "label_distribution_annotator_2": self.label_distribution_2,
        }


@dataclass(frozen=True)
class ClassificationEvaluationResult:
    """Classifier performance against gold/adjudicated annotations."""
    total_evaluated: int
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    per_class_metrics: Dict[str, Dict[str, float]]
    confusion_matrix: Dict[str, Dict[str, int]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_evaluated": self.total_evaluated,
            "accuracy": round(self.accuracy, 4),
            "macro_precision": round(self.macro_precision, 4),
            "macro_recall": round(self.macro_recall, 4),
            "macro_f1": round(self.macro_f1, 4),
            "per_class_metrics": {
                c: {k: round(v, 4) for k, v in metrics.items()}
                for c, metrics in self.per_class_metrics.items()
            },
            "confusion_matrix": self.confusion_matrix,
        }


def compute_inter_annotator_agreement(
    annotator_1: Sequence[str],
    annotator_2: Sequence[str],
) -> InterAnnotatorAgreementResult:
    """
    Compute raw percentage agreement and Cohen's Kappa between two annotators.
    """
    if len(annotator_1) != len(annotator_2):
        raise ValueError(
            f"Annotator lengths mismatch: {len(annotator_1)} vs {len(annotator_2)}"
        )

    n = len(annotator_1)
    if n == 0:
        return InterAnnotatorAgreementResult(
            total_items=0,
            agreed_items=0,
            raw_agreement=0.0,
            cohens_kappa=0.0,
            label_distribution_1={},
            label_distribution_2={},
        )

    # Clean and uppercase
    a1 = [str(x).strip().upper() for x in annotator_1]
    a2 = [str(x).strip().upper() for x in annotator_2]

    # Raw agreement
    agreed = sum(1 for x, y in zip(a1, a2) if x == y)
    p_o = agreed / n

    # Marginals for Cohen's Kappa
    counts_1 = Counter(a1)
    counts_2 = Counter(a2)
    all_categories = sorted(set(counts_1.keys()) | set(counts_2.keys()))

    p_e = sum((counts_1[cat] / n) * (counts_2[cat] / n) for cat in all_categories)

    if p_e >= 1.0:
        kappa = 1.0 if p_o == 1.0 else 0.0
    else:
        kappa = (p_o - p_e) / (1.0 - p_e)

    return InterAnnotatorAgreementResult(
        total_items=n,
        agreed_items=agreed,
        raw_agreement=p_o,
        cohens_kappa=kappa,
        label_distribution_1=dict(counts_1),
        label_distribution_2=dict(counts_2),
    )


def evaluate_classification_against_gold(
    gold_labels: Sequence[str],
    pred_labels: Sequence[str],
    target_classes: Optional[Sequence[str]] = None,
) -> ClassificationEvaluationResult:
    """
    Calculate classification performance of system predictions against gold adjudicated labels.
    """
    if len(gold_labels) != len(pred_labels):
        raise ValueError(
            f"Labels length mismatch: gold has {len(gold_labels)}, pred has {len(pred_labels)}"
        )

    n = len(gold_labels)
    if n == 0:
        return ClassificationEvaluationResult(
            total_evaluated=0,
            accuracy=0.0,
            macro_precision=0.0,
            macro_recall=0.0,
            macro_f1=0.0,
            per_class_metrics={},
            confusion_matrix={},
        )

    gold = [str(x).strip().upper() for x in gold_labels]
    pred = [str(x).strip().upper() for x in pred_labels]

    if target_classes:
        classes = sorted(set(str(c).strip().upper() for c in target_classes))
    else:
        classes = sorted(set(gold) | set(pred))

    # Confusion matrix: true_label -> {pred_label: count}
    confusion: Dict[str, Dict[str, int]] = {c: {c2: 0 for c2 in classes} for c in classes}
    for g, p in zip(gold, pred):
        if g in confusion and p in confusion[g]:
            confusion[g][p] += 1

    # Accuracy
    correct = sum(1 for g, p in zip(gold, pred) if g == p)
    accuracy = correct / n

    # Per-class metrics
    per_class: Dict[str, Dict[str, float]] = {}
    precisions: List[float] = []
    recalls: List[float] = []
    f1s: List[float] = []

    for c in classes:
        tp = confusion[c][c]
        fp = sum(confusion[other][c] for other in classes if other != c)
        fn = sum(confusion[c][other] for other in classes if other != c)
        support = sum(confusion[c].values())

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[c] = {
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "support": float(support),
        }
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    num_classes = max(1, len(classes))
    macro_p = sum(precisions) / num_classes
    macro_r = sum(recalls) / num_classes
    macro_f = sum(f1s) / num_classes

    return ClassificationEvaluationResult(
        total_evaluated=n,
        accuracy=accuracy,
        macro_precision=macro_p,
        macro_recall=macro_r,
        macro_f1=macro_f,
        per_class_metrics=per_class,
        confusion_matrix=confusion,
    )
