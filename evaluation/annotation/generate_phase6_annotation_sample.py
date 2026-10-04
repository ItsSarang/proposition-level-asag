"""Phase 6: Human Proposition-Level Annotation Dataset Preparation Script.

Generates a stratified, representative, and strictly blinded 500-item sample
from the frozen Experiment 4 proposition outputs (4,695 propositions across 81 questions).

Outputs:
- evaluation/annotation/master_annotation_dataset.csv (complete provenance and system predictions)
- evaluation/annotation/annotator_1.csv (strictly blinded: NO system labels, NO human grades)
- evaluation/annotation/annotator_2.csv (strictly blinded: NO system labels, NO human grades)
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
import random
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RANDOM_SEED = 42
TARGET_SAMPLE_SIZE = 500


def audit_eligibility(
    p: Dict[str, Any],
    rec: Optional[Dict[str, Any]],
    seen_student_props: Set[Tuple[str, str, str]],
) -> Tuple[bool, Optional[str]]:
    """Determine whether a proposition is eligible for human annotation.

    Exclusion categories:
    - MISSING_CONTEXT
    - EMPTY_TEXT
    - DUPLICATE_ARTIFACT
    - TRUNCATED_TEXT
    - UNINTERPRETABLE_FRAGMENT
    - INVALID_SPAN
    - OTHER_EXTRACTION_ARTIFACT
    """
    qid = p.get("question_id", "")
    s_idx = str(p.get("student_index", ""))
    text = p.get("proposition_text", "").strip()

    # 1. Missing context
    if not rec or not rec.get("student_answer_cleaned") or not rec.get("question"):
        return False, "MISSING_CONTEXT"

    # 2. Empty text
    if not text:
        return False, "EMPTY_TEXT"

    # 3. Duplicate artifact within same student answer
    dup_key = (qid, s_idx, text.lower())
    if dup_key in seen_student_props:
        return False, "DUPLICATE_ARTIFACT"

    # 4. Truncated text (e.g. unclosed parentheses in asymptotic notation, trailing hyphens)
    if (
        (text.startswith("O(") and not text.endswith(")"))
        or (text.endswith("-") and len(text.split()) == 1)
        or (text.startswith("-") and len(text.split()) == 1)
    ):
        return False, "TRUNCATED_TEXT"

    # 5. Uninterpretable fragments (lone punctuation, symbols, lone non-content stopwords/abbreviations)
    if re.match(r"^[\W_]+$", text):
        return False, "UNINTERPRETABLE_FRAGMENT"

    lone_non_content = {
        "do", "is", "are", "was", "were", "can", "could", "may", "might",
        "must", "shall", "should", "will", "would", "re", "ex"
    }
    if text.lower() in lone_non_content:
        return False, "UNINTERPRETABLE_FRAGMENT"

    # 6. Invalid span (text or its content words cannot be found in student answer)
    student_ans = rec["student_answer_cleaned"].lower()
    if text.lower() not in student_ans:
        t_tokens = set(re.findall(r"\w+", text.lower()))
        s_tokens = set(re.findall(r"\w+", student_ans))
        if not t_tokens or len(t_tokens & s_tokens) / len(t_tokens) < 0.30:
            return False, "INVALID_SPAN"

    # 7. Other extraction artifacts (garbled character encodings)
    if "â€" in text or "\ufffd" in text:
        return False, "OTHER_EXTRACTION_ARTIFACT"

    return True, None


def create_highlighted_context(student_answer: str, proposition_text: str) -> str:
    """Create a student answer context with the target proposition clearly demarcated."""
    p_clean = proposition_text.strip()

    # 1. Exact match
    idx = student_answer.find(p_clean)
    if idx != -1:
        return (
            student_answer[:idx]
            + ">>> "
            + student_answer[idx : idx + len(p_clean)]
            + " <<<"
            + student_answer[idx + len(p_clean) :]
        )

    # 2. Case-insensitive exact match
    pattern = re.compile(re.escape(p_clean), re.IGNORECASE)
    match = pattern.search(student_answer)
    if match:
        s, e = match.span()
        return (
            student_answer[:s]
            + ">>> "
            + student_answer[s:e]
            + " <<<"
            + student_answer[e:]
        )

    # 3. Fuzzy whitespace token match
    tokens = [re.escape(w) for w in p_clean.split()]
    fuzzy_pattern = re.compile(r"\s+".join(tokens), re.IGNORECASE)
    match = fuzzy_pattern.search(student_answer)
    if match:
        s, e = match.span()
        return (
            student_answer[:s]
            + ">>> "
            + student_answer[s:e]
            + " <<<"
            + student_answer[e:]
        )

    # 4. Fallback if substring cannot be cleanly bounded
    return f"[TARGET PROPOSITION: {p_clean}]\nSTUDENT ANSWER: {student_answer}"


def sample_stratified_by_question(
    candidates: List[Dict[str, Any]], target_n: int, seed: int
) -> List[Dict[str, Any]]:
    """Sample candidates round-robin across questions to guarantee broad benchmark coverage."""
    rng = random.Random(seed)
    by_q: Dict[str, List[Dict[str, Any]]] = {}
    for c in candidates:
        qid = c["question_id"]
        if qid not in by_q:
            by_q[qid] = []
        by_q[qid].append(c)

    for qid in by_q:
        rng.shuffle(by_q[qid])

    selected: List[Dict[str, Any]] = []
    q_keys = sorted(by_q.keys())
    round_idx = 0
    while len(selected) < target_n:
        added_in_round = False
        for q in q_keys:
            if len(selected) >= target_n:
                break
            if round_idx < len(by_q[q]):
                selected.append(by_q[q][round_idx])
                added_in_round = True
        if not added_in_round:
            break
        round_idx += 1

    return selected


def run_sampling() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    active_csv_path = repo_root / "data/processed/mohler_asag/mohler_asag_active.csv"
    props_json_path = (
        repo_root / "evaluation/experiments/experiment_4/experiment_4_propositions.json"
    )
    annotation_dir = repo_root / "evaluation/annotation"
    annotation_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading active Mohler dataset from %s...", active_csv_path)
    with open(active_csv_path, encoding="utf-8") as f:
        records = {(r["question_id"], r["student_index"]): r for r in csv.DictReader(f)}

    logger.info("Loading frozen Experiment 4 propositions from %s...", props_json_path)
    with open(props_json_path, encoding="utf-8") as f:
        props = json.load(f)

    logger.info("Total propositions loaded: %d", len(props))

    # 1. Eligibility Audit
    eligible_props: List[Dict[str, Any]] = []
    ineligible_counts: Dict[str, int] = {}
    seen_student_props: Set[Tuple[str, str, str]] = set()

    # Track proposition index per student answer to generate unique IDs
    student_prop_counters: Dict[Tuple[str, str], int] = {}

    for idx, p in enumerate(props):
        qid = str(p["question_id"])
        s_idx = str(p["student_index"])
        rec = records.get((qid, s_idx))

        is_el, reason = audit_eligibility(p, rec, seen_student_props)
        if not is_el:
            assert reason is not None
            ineligible_counts[reason] = ineligible_counts.get(reason, 0) + 1
            continue

        text = p["proposition_text"].strip()
        seen_student_props.add((qid, s_idx, text.lower()))

        # Increment local proposition counter
        counter_key = (qid, s_idx)
        p_num = student_prop_counters.get(counter_key, 0) + 1
        student_prop_counters[counter_key] = p_num

        assert rec is not None
        asgn = int(rec["assignment"])
        q_idx = int(rec["question_index"])

        item_dict = {
            "source_index": idx,
            "question_id": qid,
            "assignment": asgn,
            "question_index": q_idx,
            "student_index": int(s_idx),
            "answer_id": f"ANS_{asgn}_{q_idx}_{s_idx}",
            "proposition_id": f"PROP_{asgn}_{q_idx}_{s_idx}_{p_num}",
            "question_text": rec["question"].strip(),
            "reference_text": rec["reference_answer"].strip(),
            "student_answer_text": rec["student_answer_cleaned"].strip(),
            "proposition_text": text,
            "proposition_context": create_highlighted_context(
                rec["student_answer_cleaned"].strip(), text
            ),
            "system_label": p["classification"],
            "system_severity": p["severity_level"],
            "system_rationale": p["rationale"],
        }
        eligible_props.append(item_dict)

    logger.info(
        "Eligibility Audit Complete: %d eligible (%.2f%%), %d excluded (%.2f%%)",
        len(eligible_props),
        len(eligible_props) / len(props) * 100.0,
        len(props) - len(eligible_props),
        (len(props) - len(eligible_props)) / len(props) * 100.0,
    )
    for r_name, r_cnt in sorted(ineligible_counts.items()):
        logger.info("  Exclusion Reason [%s]: %d", r_name, r_cnt)

    # 2. Stratified Sampling
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for p in eligible_props:
        cat = p["system_label"]
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(p)

    logger.info("Eligible pool by category:")
    for c_name, c_list in sorted(by_cat.items()):
        logger.info("  %s: %d (%.2f%%)", c_name, len(c_list), len(c_list) / len(eligible_props) * 100.0)

    # Targeted inclusion of all eligible INCORRECT cases
    sample_incorrect = list(by_cat.get("INCORRECT", []))
    n_incorrect = len(sample_incorrect)

    # Remaining items allocated equally between UNCERTAIN and IRRELEVANT
    remaining_target = TARGET_SAMPLE_SIZE - n_incorrect
    target_uncertain = remaining_target // 2  # 218
    target_irrelevant = remaining_target - target_uncertain  # 218

    logger.info(
        "Sampling allocation: INCORRECT=%d, UNCERTAIN=%d, IRRELEVANT=%d (Total=%d)",
        n_incorrect,
        target_uncertain,
        target_irrelevant,
        TARGET_SAMPLE_SIZE,
    )

    sample_uncertain = sample_stratified_by_question(
        by_cat.get("UNCERTAIN", []), target_uncertain, seed=RANDOM_SEED
    )
    sample_irrelevant = sample_stratified_by_question(
        by_cat.get("IRRELEVANT", []), target_irrelevant, seed=RANDOM_SEED + 1
    )

    full_sample = sample_incorrect + sample_uncertain + sample_irrelevant
    assert len(full_sample) == TARGET_SAMPLE_SIZE, f"Sample size mismatch: {len(full_sample)}"

    # Deterministic final shuffle
    final_rng = random.Random(RANDOM_SEED)
    final_rng.shuffle(full_sample)

    # Assign sequential item_id (ITEM_001 to ITEM_500)
    for i, item in enumerate(full_sample, start=1):
        item["item_id"] = f"ITEM_{i:03d}"

    # 3. Export Master Dataset
    master_csv_path = annotation_dir / "master_annotation_dataset.csv"
    master_fields = [
        "item_id",
        "question_id",
        "answer_id",
        "proposition_id",
        "question_text",
        "reference_text",
        "student_answer_text",
        "proposition_text",
        "proposition_context",
        "system_label",
        "system_severity",
        "system_rationale",
        "annotator_1_label",
        "annotator_1_notes",
        "annotator_2_label",
        "annotator_2_notes",
        "adjudicated_label",
        "adjudication_notes",
    ]

    with open(master_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=master_fields)
        writer.writeheader()
        for item in full_sample:
            row = {k: item.get(k, "") for k in master_fields}
            writer.writerow(row)
    logger.info("Exported master annotation dataset: %s", master_csv_path)

    # 4. Export Blinded Annotator 1 and Annotator 2 Datasets
    blinded_fields = [
        "item_id",
        "question_id",
        "answer_id",
        "proposition_id",
        "question_text",
        "reference_text",
        "student_answer_text",
        "proposition_text",
        "proposition_context",
        "annotator_label",
        "annotator_notes",
    ]

    for ann_name in ["annotator_1.csv", "annotator_2.csv"]:
        ann_path = annotation_dir / ann_name
        with open(ann_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=blinded_fields)
            writer.writeheader()
            for item in full_sample:
                row = {
                    "item_id": item["item_id"],
                    "question_id": item["question_id"],
                    "answer_id": item["answer_id"],
                    "proposition_id": item["proposition_id"],
                    "question_text": item["question_text"],
                    "reference_text": item["reference_text"],
                    "student_answer_text": item["student_answer_text"],
                    "proposition_text": item["proposition_text"],
                    "proposition_context": item["proposition_context"],
                    "annotator_label": "",
                    "annotator_notes": "",
                }
                writer.writerow(row)
        logger.info("Exported blinded dataset: %s", ann_path)

    # 5. Automated Blinding Verification Check
    logger.info("Running automated blinding verification...")
    forbidden_tokens = ["system_label", "system_severity", "system_rationale", "human_score", "human_grade"]
    for ann_name in ["annotator_1.csv", "annotator_2.csv"]:
        ann_path = annotation_dir / ann_name
        with open(ann_path, encoding="utf-8") as f:
            content = f.read()

        # Check headers and content for forbidden fields
        for ft in forbidden_tokens:
            if ft in content:
                raise ValueError(f"Blinding violation! Found '{ft}' in {ann_name}")

        # Check that empty label columns are truly empty in data rows
        reader = csv.DictReader(content.splitlines())
        for r_idx, r in enumerate(reader):
            if r["annotator_label"].strip() != "":
                raise ValueError(f"Blinding violation! Non-empty annotator_label at row {r_idx} in {ann_name}")
            if r["annotator_notes"].strip() != "":
                raise ValueError(f"Blinding violation! Non-empty annotator_notes at row {r_idx} in {ann_name}")

    logger.info("Blinding verification passed successfully: NO system labels, NO severities, NO grades exposed.")


if __name__ == "__main__":
    run_sampling()
