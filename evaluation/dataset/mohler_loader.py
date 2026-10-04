"""Mohler ASAG Dataset Loader and Structured Container.

This module provides data structures and loading utilities for the University of
North Texas Computer Science Short Answer Dataset Version 2.0 (Mohler et al., 2011).

Research Context:
Stage 15 evaluates three ASAG systems against human grades:
1. TF-IDF + Cosine Baseline
2. Base ASAG (Basak-inspired)
3. Proposed ASAG (Proposition-level extension)

Dataset Facts (UNT CS Short Answer Dataset v2.0):
- Total questions: 87 (across 10 assignments and 2 exams).
- Active questions: 81 (6 questions starting with '#' in data/docs/files are
  selection/ordering questions and ignored in published literature).
- Total student answers: 2,442 across all 87 questions.
- Active student answers: 2,273 across 81 active questions (matching ACL 2011).
- Human graders: Grader 1 ('other', class TA) and Grader 2 ('me', Michael Mohler).
- Assignments 1-10: 1,721 active records graded on integer 0..5 scale.
- Exams 11-12: 552 active records graded on 0..10 scale, with official 'ave'
  normalized to 0..5 scale.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple
import pandas as pd


@dataclass(frozen=True)
class MohlerRecord:
    """Individual student answer record from the Mohler ASAG dataset.

    Attributes:
        question_id: The original identifier (e.g. "1.1", "12.10").
        assignment: 1-based assignment/exam number (1..12).
        question_index: 1-based question number within the assignment (1..10).
        is_active: True if the question is an active short-answer question;
            False if marked with '#' (selection/ordering question).
        student_index: 0-based index of the student answer for this question.
        question: Question text with question_id prefix removed.
        reference_answer: Instructor answer with question_id prefix removed.
        student_answer_raw: Raw student answer text with prefix removed,
            preserving internal HTML tags (e.g., <br>).
        student_answer_cleaned: Cleaned student answer text with HTML tags
            removed and whitespace normalized.
        score_me: Grader 2 score (Michael Mohler).
        score_other: Grader 1 score (Course TA).
        score_ave: Official average score reported in data/scores/x.y/ave
            (on 0..5 scale).
        score_scale: Grading scale descriptor: '0-5' for assignments 1-10,
            or '0-10_normalized_to_0-5' for exams 11-12.
    """

    question_id: str
    assignment: int
    question_index: int
    is_active: bool
    student_index: int
    question: str
    reference_answer: str
    student_answer_raw: str
    student_answer_cleaned: str
    score_me: float
    score_other: float
    score_ave: float
    score_scale: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a standard dictionary."""
        return asdict(self)


class MohlerDataset:
    """Immutable collection of MohlerRecord instances with filtering utilities."""

    def __init__(self, records: Sequence[MohlerRecord]) -> None:
        self._records: Tuple[MohlerRecord, ...] = tuple(records)

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[MohlerRecord]:
        return iter(self._records)

    def __getitem__(self, idx: int) -> MohlerRecord:
        return self._records[idx]

    @property
    def records(self) -> Tuple[MohlerRecord, ...]:
        """All records in this dataset."""
        return self._records

    def filter_active(self) -> MohlerDataset:
        """Filter to the 81 active questions (excluding 6 selection/ordering '#')."""
        return MohlerDataset([r for r in self._records if r.is_active])

    def filter_assignments_1_10(self) -> MohlerDataset:
        """Filter to active records from Assignments 1-10 (uniform 0-5 scale)."""
        return MohlerDataset([r for r in self._records if r.is_active and r.assignment <= 10])

    def filter_exams(self) -> MohlerDataset:
        """Filter to active records from Exams 11-12."""
        return MohlerDataset([r for r in self._records if r.is_active and r.assignment > 10])

    def filter_by_question(self, question_id: str) -> MohlerDataset:
        """Filter to records belonging to a specific question ID."""
        clean_id = question_id.lstrip("#")
        return MohlerDataset([r for r in self._records if r.question_id == clean_id])

    def filter_by_assignment(self, assignment: int) -> MohlerDataset:
        """Filter to records belonging to a specific assignment number."""
        return MohlerDataset([r for r in self._records if r.assignment == assignment])

    def get_questions_summary(self) -> List[Dict[str, Any]]:
        """Return metadata summary for each unique question in the dataset."""
        questions_map: Dict[str, Dict[str, Any]] = {}
        for r in self._records:
            if r.question_id not in questions_map:
                questions_map[r.question_id] = {
                    "question_id": r.question_id,
                    "assignment": r.assignment,
                    "question_index": r.question_index,
                    "is_active": r.is_active,
                    "question_text": r.question,
                    "reference_answer": r.reference_answer,
                    "score_scale": r.score_scale,
                    "total_student_answers": 0,
                }
            questions_map[r.question_id]["total_student_answers"] += 1
        return list(questions_map.values())

    def to_dataframe(self) -> pd.DataFrame:
        """Convert all records to a pandas DataFrame."""
        return pd.DataFrame([r.to_dict() for r in self._records])


class MohlerLoader:
    """Loader and exporter for the Mohler ASAG dataset."""

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """Strip HTML tags (e.g. <br>) and normalize whitespace.

        Implementation Decision:
        In the raw Mohler dataset, 260 student answers contain HTML <br> tags.
        These are line break artifacts from the submission web form.
        We replace <br> with a single space and collapse multiple whitespace
        characters so linguistic parsers (spaCy) receive coherent sentence text.
        """
        # Replace <br> or <br/> or <br /> with space
        cleaned = re.sub(r"<br\s*/?>", " ", raw_text, flags=re.IGNORECASE)
        # Remove any other stray HTML tags
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        # Collapse multiple whitespace and strip
        return " ".join(cleaned.split()).strip()

    @staticmethod
    def strip_prefix(line: str, prefix_id: str) -> str:
        """Strip the 'x.y ' prefix from a raw dataset line."""
        clean_id = prefix_id.lstrip("#")
        prefix = f"{clean_id} "
        if line.startswith(prefix):
            return line[len(prefix):].rstrip("\r\n")
        return line.rstrip("\r\n")

    @classmethod
    def load_raw(
        cls,
        raw_root: Optional[Path] = None,
    ) -> MohlerDataset:
        """Parse the raw UNT CS Short Answer Dataset v2.0 files.

        Args:
            raw_root: Path to the raw data directory containing data/docs/files,
                data/raw/, and data/scores/. If None, defaults to:
                <repo_root>/data/raw/mohler_asag/data

        Returns:
            MohlerDataset containing all 2,442 parsed student answers.
        """
        if raw_root is None:
            # Default to repo data/raw/mohler_asag/data
            repo_root = Path(__file__).resolve().parent.parent.parent
            raw_root = repo_root / "data" / "raw" / "mohler_asag" / "data"

        files_list_path = raw_root / "docs" / "files"
        raw_questions_path = raw_root / "raw" / "questions"
        raw_answers_path = raw_root / "raw" / "answers"

        if not files_list_path.exists():
            raise FileNotFoundError(f"Missing files list at: {files_list_path}")

        # 1. Read question file IDs from docs/files
        with open(files_list_path, "r", encoding="utf-8") as f:
            file_entries = [line.strip() for line in f if line.strip()]

        # 2. Read raw questions
        with open(raw_questions_path, "r", encoding="utf-8", errors="replace") as f:
            q_lines = [line.rstrip("\r\n") for line in f if line.strip()]

        # 3. Read raw reference answers
        with open(raw_answers_path, "r", encoding="utf-8", errors="replace") as f:
            a_lines = [line.rstrip("\r\n") for line in f if line.strip()]

        if len(file_entries) != len(q_lines) or len(file_entries) != len(a_lines):
            raise ValueError(
                f"Mismatch in question counts: files={len(file_entries)}, "
                f"questions={len(q_lines)}, answers={len(a_lines)}"
            )

        records: List[MohlerRecord] = []

        for file_entry, q_line, a_line in zip(file_entries, q_lines, a_lines):
            is_active = not file_entry.startswith("#")
            clean_id = file_entry.lstrip("#")
            parts = clean_id.split(".")
            assignment = int(parts[0])
            question_idx = int(parts[1])

            # Strip ID prefixes
            question_text = cls.strip_prefix(q_line, clean_id).strip()
            reference_text = cls.strip_prefix(a_line, clean_id).strip()

            # Paths for this question
            student_file = raw_root / "raw" / clean_id
            ave_score_file = raw_root / "scores" / clean_id / "ave"
            me_score_file = raw_root / "scores" / clean_id / "me"
            other_score_file = raw_root / "scores" / clean_id / "other"

            # Read student answers (using utf-8 with replace fallback for robust non-ASCII handling)
            with open(student_file, "r", encoding="utf-8", errors="replace") as f:
                student_lines = [l.rstrip("\r\n") for l in f if l.strip()]

            with open(ave_score_file, "r", encoding="utf-8") as f:
                ave_scores = [float(l.strip()) for l in f if l.strip()]

            with open(me_score_file, "r", encoding="utf-8") as f:
                me_scores = [float(l.strip()) for l in f if l.strip()]

            with open(other_score_file, "r", encoding="utf-8") as f:
                other_scores = [float(l.strip()) for l in f if l.strip()]

            if not (len(student_lines) == len(ave_scores) == len(me_scores) == len(other_scores)):
                raise ValueError(
                    f"Line count mismatch for {clean_id}: "
                    f"students={len(student_lines)}, ave={len(ave_scores)}, "
                    f"me={len(me_scores)}, other={len(other_scores)}"
                )

            scale_desc = "0-5" if assignment <= 10 else "0-10_normalized_to_0-5"

            for s_idx, (s_raw_line, s_ave, s_me, s_other) in enumerate(
                zip(student_lines, ave_scores, me_scores, other_scores)
            ):
                raw_ans = cls.strip_prefix(s_raw_line, clean_id)
                clean_ans = cls.clean_text(raw_ans)

                records.append(
                    MohlerRecord(
                        question_id=clean_id,
                        assignment=assignment,
                        question_index=question_idx,
                        is_active=is_active,
                        student_index=s_idx,
                        question=question_text,
                        reference_answer=reference_text,
                        student_answer_raw=raw_ans,
                        student_answer_cleaned=clean_ans,
                        score_me=s_me,
                        score_other=s_other,
                        score_ave=s_ave,
                        score_scale=scale_desc,
                    )
                )

        return MohlerDataset(records)

    @classmethod
    def load_processed_csv(
        cls,
        csv_path: Optional[Path] = None,
    ) -> MohlerDataset:
        """Load records from a processed CSV file."""
        if csv_path is None:
            repo_root = Path(__file__).resolve().parent.parent.parent
            csv_path = repo_root / "data" / "processed" / "mohler_asag" / "mohler_asag_all.csv"

        if not csv_path.exists():
            raise FileNotFoundError(f"Processed CSV not found at: {csv_path}")

        records: List[MohlerRecord] = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(
                    MohlerRecord(
                        question_id=row["question_id"],
                        assignment=int(row["assignment"]),
                        question_index=int(row["question_index"]),
                        is_active=row["is_active"].strip().lower() in ("true", "1", "yes"),
                        student_index=int(row["student_index"]),
                        question=row["question"],
                        reference_answer=row["reference_answer"],
                        student_answer_raw=row["student_answer_raw"],
                        student_answer_cleaned=row["student_answer_cleaned"],
                        score_me=float(row["score_me"]),
                        score_other=float(row["score_other"]),
                        score_ave=float(row["score_ave"]),
                        score_scale=row["score_scale"],
                    )
                )

        return MohlerDataset(records)

    @classmethod
    def export_processed_csvs(
        cls,
        output_dir: Optional[Path] = None,
        dataset: Optional[MohlerDataset] = None,
    ) -> Dict[str, Path]:
        """Export standardized processed CSV datasets.

        Creates four CSV files:
        1. mohler_asag_all.csv: All 2,442 records across 87 questions.
        2. mohler_asag_active.csv: The 2,273 active records across 81 questions.
        3. mohler_asag_assignments_1_10.csv: The 1,721 active assignment records (0-5 scale).
        4. mohler_questions.csv: 87 questions summary metadata table.

        Returns:
            Dictionary mapping dataset name to exported Path.
        """
        repo_root = Path(__file__).resolve().parent.parent.parent
        if output_dir is None:
            output_dir = repo_root / "data" / "processed" / "mohler_asag"
        output_dir.mkdir(parents=True, exist_ok=True)

        if dataset is None:
            dataset = cls.load_raw()

        # 1. mohler_asag_all.csv
        all_df = dataset.to_dataframe()
        all_path = output_dir / "mohler_asag_all.csv"
        all_df.to_csv(all_path, index=False, encoding="utf-8")

        # 2. mohler_asag_active.csv
        active_dataset = dataset.filter_active()
        active_df = active_dataset.to_dataframe()
        active_path = output_dir / "mohler_asag_active.csv"
        active_df.to_csv(active_path, index=False, encoding="utf-8")

        # 3. mohler_asag_assignments_1_10.csv
        assign_dataset = dataset.filter_assignments_1_10()
        assign_df = assign_dataset.to_dataframe()
        assign_path = output_dir / "mohler_asag_assignments_1_10.csv"
        assign_df.to_csv(assign_path, index=False, encoding="utf-8")

        # 4. mohler_questions.csv
        q_summary = dataset.get_questions_summary()
        q_df = pd.DataFrame(q_summary)
        q_path = output_dir / "mohler_questions.csv"
        q_df.to_csv(q_path, index=False, encoding="utf-8")

        return {
            "all": all_path,
            "active": active_path,
            "assignments_1_10": assign_path,
            "questions": q_path,
        }
