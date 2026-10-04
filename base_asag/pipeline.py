"""
Base ASAG Integrated Pipeline Module (Stage 10).

Integrates the completed Base ASAG components (Stages 3–9) into a single,
transparent, reproducible end-to-end grading engine:
1. Stage 3: Linguistic Preprocessing (TextPreprocessor)
2. Stage 4: Dependency Parsing (DependencyParser)
3. Stage 5: Dependency Triples / Relations (DependencyTripleExtractor)
4. Stage 6: Lexical & Semantic Relationships (LexicalSemanticComparator)
5. Stage 7: Role-Preserving Triple Matching (TripleMatcher)
6. Stage 8: Proposition-Level Textual Entailment (PropositionalEntailmentAnalyzer)
7. Stage 9: Base ASAG Scoring (BaseASAGScorer)

Methodological Foundation:
--------------------------
Inspired by the classical ASAG methodology of Basak et al. (2019)
("Short-answer grading using textual entailment"), where student answers are
evaluated on how much of the reference answer's propositional content is entailed.

Key Research Boundaries:
-----------------------
- Operates strictly as the Base ASAG baseline (System 2).
- Reference propositions are the primary scoring criteria.
- Unmatched student relations are explicitly preserved and exposed in diagnostics,
  contributing exactly 0.0 to the Base score (neither bonus nor penalty).
- Does NOT classify unmatched student information as correct, irrelevant, or incorrect
  (reserved for the proposed extension in Stages 11–14).
- Does NOT employ deep neural sentence embeddings, whole-sentence cosine similarity,
  or large language models.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union

from base_asag.dependency.parser import DependencyParser, ParsedDocument
from base_asag.dependency.triples import (
    DependencyRelation,
    DependencyTripleExtractor,
    DocumentTriples,
)
from base_asag.entailment.analyzer import (
    EntailmentResult,
    PropositionalEntailmentAnalyzer,
)
from base_asag.matching.triple_matcher import MatchedRelation, MatchingResult, TripleMatcher
from base_asag.preprocessing.processor import ProcessedDocument, TextPreprocessor
from base_asag.scoring.base_scorer import BaseASAGScorer, BaseScoreResult, PropositionScoreRecord
from base_asag.semantic.relations import LexicalSemanticComparator


@dataclass(frozen=True)
class BaseASAGPipelineResult:
    """
    Comprehensive, inspectable result of an end-to-end Base ASAG evaluation.

    Attributes
    ----------
    question : str
        The input question text.
    reference_answer : str
        The input reference answer text.
    student_answer : str
        The input student answer text.
    normalized_score : float
        The core Base ASAG grade normalized in [0.0, 1.0].
    scoring_result : BaseScoreResult
        Complete Stage 9 scoring result with itemized proposition contributions.
    matching_result : MatchingResult
        Stage 7 relational matching result.
    entailment_results : List[EntailmentResult]
        Stage 8 proposition-level entailment judgments.
    matched_relations : List[MatchedRelation]
        Aligned reference-student relation pairs.
    unmatched_reference_relations : List[DependencyRelation]
        Reference propositions not addressed by the student answer.
    unmatched_student_relations : List[DependencyRelation]
        Student relations not aligned to any reference proposition (preserved for Stage 11–14).
    reference_triples : DocumentTriples
        Extracted Stage 5 dependency relations and arcs for the reference answer.
    student_triples : DocumentTriples
        Extracted Stage 5 dependency relations and arcs for the student answer.
    reference_parsed : ParsedDocument
        Stage 4 parsed syntactic dependency tree for the reference answer.
    student_parsed : ParsedDocument
        Stage 4 parsed syntactic dependency tree for the student answer.
    question_parsed : Optional[ParsedDocument]
        Stage 4 parsed syntactic dependency tree for the question.
    """
    question: str
    reference_answer: str
    student_answer: str
    normalized_score: float
    scoring_result: BaseScoreResult
    matching_result: MatchingResult
    entailment_results: List[EntailmentResult]
    matched_relations: List[MatchedRelation]
    unmatched_reference_relations: List[DependencyRelation]
    unmatched_student_relations: List[DependencyRelation]
    reference_triples: DocumentTriples
    student_triples: DocumentTriples
    reference_parsed: ParsedDocument
    student_parsed: ParsedDocument
    question_parsed: Optional[ParsedDocument] = None

    @property
    def total_reference_propositions(self) -> int:
        """Total number of reference propositions evaluated."""
        return self.scoring_result.total_reference_propositions

    @property
    def matched_count(self) -> int:
        """Number of reference-student proposition matches."""
        return len(self.matched_relations)

    @property
    def entailed_count(self) -> int:
        """Number of reference propositions successfully entailed."""
        return self.scoring_result.entailed_count

    @property
    def uncertain_count(self) -> int:
        """Number of reference propositions evaluated as uncertain."""
        return self.scoring_result.uncertain_count

    @property
    def contradicted_count(self) -> int:
        """Number of reference propositions contradicted."""
        return self.scoring_result.contradicted_count

    @property
    def missing_count(self) -> int:
        """Number of reference propositions omitted."""
        return self.scoring_result.missing_count

    @property
    def unmatched_student_count(self) -> int:
        """Number of student propositions not aligned to the reference answer."""
        return len(self.unmatched_student_relations)

    def scale_score(self, max_points: float = 5.0) -> float:
        """
        Scale the normalized score [0, 1] to an arbitrary numeric range [0, max_points].

        Parameters
        ----------
        max_points : float, default=5.0
            Maximum point scale (e.g. 5.0, 10.0, 100.0).

        Returns
        -------
        float
            Scaled score rounded to 4 decimal places.
        """
        return self.scoring_result.scale_score(max_points=max_points)

    def map_to_letter_grade(self, scale: Optional[Dict[str, float]] = None) -> str:
        """
        Map the normalized score to an optional letter grade.

        This is an optional demonstration utility and is kept strictly
        separate from the core research score.
        """
        return self.scoring_result.map_to_letter_grade(scale=scale)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entire pipeline evaluation result to dictionary format."""
        return {
            "question": self.question,
            "reference_answer": self.reference_answer,
            "student_answer": self.student_answer,
            "normalized_score": self.normalized_score,
            "total_reference_propositions": self.total_reference_propositions,
            "entailed_count": self.entailed_count,
            "uncertain_count": self.uncertain_count,
            "contradicted_count": self.contradicted_count,
            "missing_count": self.missing_count,
            "unmatched_student_count": self.unmatched_student_count,
            "scoring_result": self.scoring_result.to_dict(),
            "matching_result": self.matching_result.to_dict(),
            "entailment_results": [e.to_dict() for e in self.entailment_results],
            "unmatched_reference_relations": [
                r.to_dict() for r in self.unmatched_reference_relations
            ],
            "unmatched_student_relations": [
                s.to_dict() for s in self.unmatched_student_relations
            ],
        }


class BaseASAGPipeline:
    """
    Integrated Base ASAG Pipeline (System 2).

    Executes the full classical pipeline from raw text inputs to final score:
        Preprocessing -> Parsing -> Triples -> Matching -> Entailment -> Scoring.

    Question Handling:
    ------------------
    The pipeline accepts `question` as part of standard ASAG input.
    The question is preprocessed and parsed. Per the existing Base ASAG
    methodology, scoring is driven by reference answer coverage; question
    relevance is not artificially invented.
    """

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        preprocessor: Optional[TextPreprocessor] = None,
        parser: Optional[DependencyParser] = None,
        extractor: Optional[DependencyTripleExtractor] = None,
        comparator: Optional[LexicalSemanticComparator] = None,
        matcher: Optional[TripleMatcher] = None,
        analyzer: Optional[PropositionalEntailmentAnalyzer] = None,
        scorer: Optional[BaseASAGScorer] = None,
        alignment_threshold: float = 0.50,
        entailment_threshold: float = 0.70,
        min_slot_similarity: float = 0.50,
        contradiction_threshold: float = 0.50,
        uncertain_weight: float = 0.50,
    ):
        """
        Initialize the complete Base ASAG pipeline.

        Parameters
        ----------
        model_name : str, default="en_core_web_sm"
            spaCy language model used for preprocessing and parsing.
        preprocessor : Optional[TextPreprocessor]
            Linguistic preprocessor (Stage 3). If None, initialized with model_name.
        parser : Optional[DependencyParser]
            Syntactic dependency parser (Stage 4). If None, initialized with model_name.
        extractor : Optional[DependencyTripleExtractor]
            Dependency triple extractor (Stage 5). If None, initialized default.
        comparator : Optional[LexicalSemanticComparator]
            Semantic comparator (Stage 6). If None, initialized default.
        matcher : Optional[TripleMatcher]
            Triple matcher (Stage 7). If None, initialized with comparator and alignment_threshold.
        analyzer : Optional[PropositionalEntailmentAnalyzer]
            Entailment analyzer (Stage 8). If None, initialized with thresholds.
        scorer : Optional[BaseASAGScorer]
            Base ASAG scorer (Stage 9). If None, initialized with uncertain_weight.
        alignment_threshold : float, default=0.50
            Stage 7 triple matching threshold.
        entailment_threshold : float, default=0.70
            Stage 8 entailment threshold.
        min_slot_similarity : float, default=0.50
            Stage 8 slot similarity threshold.
        contradiction_threshold : float, default=0.50
            Stage 8 contradiction threshold.
        uncertain_weight : float, default=0.50
            Stage 9 partial credit weight for uncertain propositions.
        """
        self.preprocessor = preprocessor or TextPreprocessor(model_name=model_name)
        self.parser = parser or DependencyParser(model_name=model_name)
        self.extractor = extractor or DependencyTripleExtractor()
        self.comparator = comparator or LexicalSemanticComparator()
        self.matcher = matcher or TripleMatcher(
            comparator=self.comparator,
            alignment_threshold=alignment_threshold,
        )
        self.analyzer = analyzer or PropositionalEntailmentAnalyzer(
            entailment_threshold=entailment_threshold,
            min_slot_similarity=min_slot_similarity,
            contradiction_threshold=contradiction_threshold,
        )
        self.scorer = scorer or BaseASAGScorer(
            uncertain_weight=uncertain_weight,
        )

    def grade(
        self,
        question: str,
        reference_answer: str,
        student_answer: str,
        reference_weights: Optional[Sequence[float]] = None,
    ) -> BaseASAGPipelineResult:
        """
        Execute the Base ASAG grading pipeline for a student response.

        Parameters
        ----------
        question : str
            The question prompt.
        reference_answer : str
            The instructor's model reference answer.
        student_answer : str
            The student's submitted response.
        reference_weights : Optional[Sequence[float]], default=None
            Optional importance weights for each reference proposition.

        Returns
        -------
        BaseASAGPipelineResult
            Complete, inspectable evaluation result.
        """
        # Validate inputs
        if question is None or not isinstance(question, str):
            raise TypeError(f"question must be a string, got {type(question).__name__}.")
        if reference_answer is None or not isinstance(reference_answer, str):
            raise TypeError(
                f"reference_answer must be a string, got {type(reference_answer).__name__}."
            )
        if student_answer is None or not isinstance(student_answer, str):
            raise TypeError(
                f"student_answer must be a string, got {type(student_answer).__name__}."
            )

        q_clean = question.strip()
        ref_clean = reference_answer.strip()
        stu_clean = student_answer.strip()

        # Handle empty reference answer
        if not ref_clean:
            raise ValueError("reference_answer cannot be empty or whitespace-only.")

        # Stage 3 & 4: Preprocessing and Dependency Parsing
        ref_parsed = self.parser.parse(self.preprocessor.process(ref_clean))
        q_parsed = self.parser.parse(self.preprocessor.process(q_clean)) if q_clean else None

        # Handle empty student answer gracefully
        if not stu_clean:
            # Student submitted empty answer
            stu_proc = self.preprocessor.process("", allow_empty=True)
            stu_parsed = self.parser.parse(stu_proc, allow_empty=True)
            ref_triples = self.extractor.extract_document(ref_parsed)
            stu_triples = self.extractor.extract_document(stu_parsed)

            matching_res = self.matcher.match(ref_triples, stu_triples)
            entailment_res = self.analyzer.evaluate_matching_result(
                matching_res, ref_parsed, stu_parsed
            )
            score_res = self.scorer.score_pipeline(
                matching_res, entailment_res, reference_weights=reference_weights
            )

            return BaseASAGPipelineResult(
                question=question,
                reference_answer=reference_answer,
                student_answer=student_answer,
                normalized_score=0.0,
                scoring_result=score_res,
                matching_result=matching_res,
                entailment_results=entailment_res,
                matched_relations=[],
                unmatched_reference_relations=matching_res.unmatched_reference_relations,
                unmatched_student_relations=[],
                reference_triples=ref_triples,
                student_triples=stu_triples,
                reference_parsed=ref_parsed,
                student_parsed=stu_parsed,
                question_parsed=q_parsed,
            )

        # Normal processing: Student answer is non-empty
        stu_parsed = self.parser.parse(self.preprocessor.process(stu_clean))

        # Stage 5: Dependency Triples / Canonical Relations
        ref_triples = self.extractor.extract_document(ref_parsed)
        stu_triples = self.extractor.extract_document(stu_parsed)

        # Stage 7: Triple Matching (using Stage 6 LexicalSemanticComparator)
        matching_res = self.matcher.match(ref_triples, stu_triples)

        # Stage 8: Proposition-Level Entailment Analysis
        entailment_res = self.analyzer.evaluate_matching_result(
            matching_res, ref_parsed, stu_parsed
        )

        # Stage 9: Base ASAG Scoring
        score_res = self.scorer.score_pipeline(
            matching_res, entailment_res, reference_weights=reference_weights
        )

        return BaseASAGPipelineResult(
            question=question,
            reference_answer=reference_answer,
            student_answer=student_answer,
            normalized_score=score_res.normalized_score,
            scoring_result=score_res,
            matching_result=matching_res,
            entailment_results=entailment_res,
            matched_relations=matching_res.matched_relations,
            unmatched_reference_relations=matching_res.unmatched_reference_relations,
            unmatched_student_relations=matching_res.unmatched_student_relations,
            reference_triples=ref_triples,
            student_triples=stu_triples,
            reference_parsed=ref_parsed,
            student_parsed=stu_parsed,
            question_parsed=q_parsed,
        )
