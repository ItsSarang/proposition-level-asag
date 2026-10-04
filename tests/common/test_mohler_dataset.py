"""Unit tests for Mohler ASAG dataset loading, cleaning, and structure (Stage 15.1)."""

from pathlib import Path
import pytest
import pandas as pd

from evaluation.dataset.mohler_loader import MohlerDataset, MohlerLoader, MohlerRecord
from evaluation.dataset.inspect_mohler import compute_dataset_stats


@pytest.fixture(scope="module")
def repo_root() -> Path:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "pyproject.toml").exists() or (p / "GEMINI.md").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def raw_dataset() -> MohlerDataset:
    return MohlerLoader.load_raw()


@pytest.fixture(scope="module")
def processed_dataset() -> MohlerDataset:
    return MohlerLoader.load_processed_csv()


# =========================================================================
# 1. Dataset Counts and Composition Tests
# =========================================================================

def test_raw_files_exist(repo_root: Path):
    """Verify raw Mohler dataset files exist in data/raw/mohler_asag/."""
    raw_dir = repo_root / "data" / "raw" / "mohler_asag" / "data"
    assert (raw_dir / "docs" / "files").exists()
    assert (raw_dir / "raw" / "questions").exists()
    assert (raw_dir / "raw" / "answers").exists()
    assert (raw_dir / "raw" / "1.1").exists()
    assert (raw_dir / "scores" / "1.1" / "ave").exists()
    assert (raw_dir / "scores" / "1.1" / "me").exists()
    assert (raw_dir / "scores" / "1.1" / "other").exists()


def test_mohler_loader_total_counts(raw_dataset: MohlerDataset):
    """Verify total record count across all 87 questions is exactly 2,442."""
    assert len(raw_dataset) == 2442


def test_mohler_dataset_active_counts(raw_dataset: MohlerDataset):
    """Verify active record count is 2,273 and ignored count is 169 (matches ACL 2011)."""
    active = raw_dataset.filter_active()
    assert len(active) == 2273
    ignored_count = len(raw_dataset) - len(active)
    assert ignored_count == 169


def test_question_counts_and_ignored_ids(raw_dataset: MohlerDataset):
    """Verify 87 total questions, 81 active questions, and the 6 specific ignored questions."""
    q_summary = raw_dataset.get_questions_summary()
    assert len(q_summary) == 87

    active_qs = [q for q in q_summary if q["is_active"]]
    ignored_qs = [q for q in q_summary if not q["is_active"]]

    assert len(active_qs) == 81
    assert len(ignored_qs) == 6

    ignored_ids = {q["question_id"] for q in ignored_qs}
    expected_ignored = {"4.6", "4.7", "8.5", "9.5", "9.7", "12.3"}
    assert ignored_ids == expected_ignored


def test_assignments_1_10_counts_and_scale(raw_dataset: MohlerDataset):
    """Verify Assignments 1-10 have 1,721 active records on the '0-5' scale."""
    a_1_10 = raw_dataset.filter_assignments_1_10()
    assert len(a_1_10) == 1721
    for r in a_1_10:
        assert r.is_active is True
        assert r.assignment <= 10
        assert r.score_scale == "0-5"


def test_exams_counts_and_scale(raw_dataset: MohlerDataset):
    """Verify Exams 11-12 have 552 active records on the '0-10_normalized_to_0-5' scale."""
    exams = raw_dataset.filter_exams()
    assert len(exams) == 552
    for r in exams:
        assert r.is_active is True
        assert r.assignment in (11, 12)
        assert r.score_scale == "0-10_normalized_to_0-5"


# =========================================================================
# 2. Score Integrity Tests
# =========================================================================

def test_assignments_1_10_average_arithmetic(raw_dataset: MohlerDataset):
    """Verify ave == (me + other) / 2.0 exactly for all records in Assignments 1-10."""
    a_1_10 = raw_dataset.filter_assignments_1_10()
    for r in a_1_10:
        expected_ave = (r.score_me + r.score_other) / 2.0
        assert abs(r.score_ave - expected_ave) < 1e-5


def test_score_ranges(raw_dataset: MohlerDataset):
    """Verify score ranges: me and other are 0-5 for A1-10, 0-10 for exams; ave is always 0-5."""
    for r in raw_dataset:
        assert 0.0 <= r.score_ave <= 5.0
        if r.assignment <= 10:
            assert 0.0 <= r.score_me <= 5.0
            assert 0.0 <= r.score_other <= 5.0
        else:
            assert 0.0 <= r.score_me <= 10.0
            assert 0.0 <= r.score_other <= 10.0


# =========================================================================
# 3. Text Cleaning and Normalization Tests
# =========================================================================

def test_clean_text_utility():
    """Verify clean_text removes <br>, collapses whitespace, and trims."""
    raw = "  This is an answer.<br><br>Second sentence.<br />  "
    cleaned = MohlerLoader.clean_text(raw)
    assert cleaned == "This is an answer. Second sentence."


def test_html_tag_preservation_and_removal(raw_dataset: MohlerDataset):
    """Verify HTML tags are preserved in student_answer_raw but removed in student_answer_cleaned."""
    records_with_html = [r for r in raw_dataset if "<br" in r.student_answer_raw.lower()]
    assert len(records_with_html) == 260
    for r in records_with_html:
        assert "<br" in r.student_answer_raw.lower()
        assert "<br" not in r.student_answer_cleaned.lower()
        assert "<" not in r.student_answer_cleaned


def test_prefix_stripping(raw_dataset: MohlerDataset):
    """Verify question ID prefix (e.g. '1.1 ') is stripped from question, answer, and student texts."""
    for r in raw_dataset:
        prefix = f"{r.question_id} "
        assert not r.question.startswith(prefix)
        assert not r.reference_answer.startswith(prefix)
        assert not r.student_answer_raw.startswith(prefix)
        assert not r.student_answer_cleaned.startswith(prefix)


def test_no_empty_answers(raw_dataset: MohlerDataset):
    """Verify no records have empty questions, reference answers, or student answers."""
    for r in raw_dataset:
        assert len(r.question) > 0
        assert len(r.reference_answer) > 0
        assert len(r.student_answer_raw) > 0
        assert len(r.student_answer_cleaned) > 0


# =========================================================================
# 4. Processed CSV and Roundtrip Tests
# =========================================================================

def test_processed_csv_files_exist(repo_root: Path):
    """Verify all 4 processed CSV files exist in data/processed/mohler_asag/."""
    proc_dir = repo_root / "data" / "processed" / "mohler_asag"
    assert (proc_dir / "mohler_asag_all.csv").exists()
    assert (proc_dir / "mohler_asag_active.csv").exists()
    assert (proc_dir / "mohler_asag_assignments_1_10.csv").exists()
    assert (proc_dir / "mohler_questions.csv").exists()


def test_processed_csv_row_counts(repo_root: Path):
    """Verify row counts in exported CSV files match expectations."""
    proc_dir = repo_root / "data" / "processed" / "mohler_asag"

    df_all = pd.read_csv(proc_dir / "mohler_asag_all.csv")
    assert len(df_all) == 2442

    df_active = pd.read_csv(proc_dir / "mohler_asag_active.csv")
    assert len(df_active) == 2273

    df_a1_10 = pd.read_csv(proc_dir / "mohler_asag_assignments_1_10.csv")
    assert len(df_a1_10) == 1721

    df_q = pd.read_csv(proc_dir / "mohler_questions.csv")
    assert len(df_q) == 87


def test_roundtrip_fidelity(raw_dataset: MohlerDataset, processed_dataset: MohlerDataset):
    """Verify processed CSV preserves all raw dataset fields without loss."""
    assert len(raw_dataset) == len(processed_dataset) == 2442

    for r_raw, r_proc in zip(raw_dataset, processed_dataset):
        assert r_raw.question_id == r_proc.question_id
        assert r_raw.assignment == r_proc.assignment
        assert r_raw.question_index == r_proc.question_index
        assert r_raw.is_active == r_proc.is_active
        assert r_raw.student_index == r_proc.student_index
        assert r_raw.question == r_proc.question
        assert r_raw.reference_answer == r_proc.reference_answer
        assert r_raw.student_answer_raw == r_proc.student_answer_raw
        assert r_raw.student_answer_cleaned == r_proc.student_answer_cleaned
        assert abs(r_raw.score_me - r_proc.score_me) < 1e-6
        assert abs(r_raw.score_other - r_proc.score_other) < 1e-6
        assert abs(r_raw.score_ave - r_proc.score_ave) < 1e-6
        assert r_raw.score_scale == r_proc.score_scale


# =========================================================================
# 5. Dataset Container Method Tests
# =========================================================================

def test_dataset_indexing_and_iteration(raw_dataset: MohlerDataset):
    """Verify dataset supports indexing, len, and iteration."""
    assert len(raw_dataset) == 2442
    rec = raw_dataset[0]
    assert isinstance(rec, MohlerRecord)
    assert rec.question_id == "1.1"
    assert rec.student_index == 0

    records_list = list(raw_dataset)
    assert len(records_list) == 2442


def test_dataset_filter_by_question(raw_dataset: MohlerDataset):
    """Verify filtering by question_id returns only records for that question."""
    q_1_1 = raw_dataset.filter_by_question("1.1")
    assert len(q_1_1) == 29
    for r in q_1_1:
        assert r.question_id == "1.1"


def test_dataset_filter_by_assignment(raw_dataset: MohlerDataset):
    """Verify filtering by assignment returns all answers for that assignment."""
    a1 = raw_dataset.filter_by_assignment(1)
    assert len(a1) == 203  # 7 questions * 29 answers
    for r in a1:
        assert r.assignment == 1


def test_dataset_to_dataframe(raw_dataset: MohlerDataset):
    """Verify to_dataframe returns a DataFrame with expected columns."""
    df = raw_dataset.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2442
    expected_cols = {
        "question_id", "assignment", "question_index", "is_active",
        "student_index", "question", "reference_answer",
        "student_answer_raw", "student_answer_cleaned",
        "score_me", "score_other", "score_ave", "score_scale"
    }
    assert expected_cols.issubset(set(df.columns))


# =========================================================================
# 6. Inspection Statistics Tests
# =========================================================================

def test_compute_dataset_stats(raw_dataset: MohlerDataset):
    """Verify compute_dataset_stats produces verified summary statistics."""
    stats = compute_dataset_stats(raw_dataset)
    assert stats["total_records"] == 2442
    assert stats["active_records"] == 2273
    assert stats["ignored_records"] == 169
    assert stats["total_questions"] == 87
    assert stats["active_questions"] == 81
    assert stats["ignored_questions"] == 6

    ir = stats["inter_rater_assignments_1_10"]
    # Check grader correlation matches ~0.5910
    assert abs(ir["pearson_r"] - 0.5910) < 0.001
    assert abs(ir["spearman_rho"] - 0.5855) < 0.001
    assert abs(ir["mae"] - 0.7263) < 0.001
    assert abs(ir["rmse"] - 1.2618) < 0.001
