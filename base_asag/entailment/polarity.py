"""
Polarity and Negation Detection Module for Base ASAG (Stage 8).

Detects grammatical and lexical negation in dependency relations and sentences.
Inspects dependency subtrees, verbal auxiliaries, and nominal determiners to
determine whether a proposition is POSITIVE or NEGATED.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from base_asag.dependency.parser import ParsedSentence, ParsedToken
from base_asag.dependency.triples import DependencyRelation


@dataclass(frozen=True)
class PolarityInfo:
    """
    Structured outcome of polarity detection for a dependency relation.

    Attributes
    ----------
    polarity : str
        "POSITIVE" or "NEGATED".
    is_negated : bool
        True if explicit negation was detected, False otherwise.
    negation_tokens : List[str]
        Surface tokens that triggered the negation classification.
    evidence : str
        Human-readable explanation of how polarity was determined.
    """
    polarity: str
    is_negated: bool
    negation_tokens: List[str]
    evidence: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert polarity information to dictionary format."""
        return {
            "polarity": self.polarity,
            "is_negated": self.is_negated,
            "negation_tokens": list(self.negation_tokens),
            "evidence": self.evidence,
        }


class PolarityDetector:
    """
    Detects polarity (POSITIVE vs NEGATED) of dependency relations.

    Methodology:
    1. If a ParsedSentence is available:
       - Inspects predicate token children for grammatical negation markers
         (dep="neg" or negative lemmas: not, n't, never, no, neither, nor).
       - Inspects auxiliary verb dependents of the predicate for negation.
       - Inspects nominal determiners of the subject and object (e.g. "no records").
    2. Fallback:
       - Lexical scan over relation tokens (predicate, subject, object).
    """

    NEGATION_LEMMAS: Set[str] = {
        "not",
        "n't",
        "never",
        "no",
        "neither",
        "nor",
        "cannot",
        "none",
    }

    def detect(
        self,
        relation: DependencyRelation,
        sentence: Optional[ParsedSentence] = None,
    ) -> PolarityInfo:
        """
        Detect polarity of a dependency relation.

        Parameters
        ----------
        relation : DependencyRelation
            The relation whose polarity is being evaluated.
        sentence : Optional[ParsedSentence], default=None
            The parsed sentence tree containing the relation tokens.

        Returns
        -------
        PolarityInfo
            Structured polarity assessment.
        """
        if not isinstance(relation, DependencyRelation):
            raise TypeError(
                f"Expected DependencyRelation, got {type(relation).__name__}."
            )

        negation_found: List[str] = []
        evidence_notes: List[str] = []

        if sentence is not None:
            if not isinstance(sentence, ParsedSentence):
                raise TypeError(
                    f"Expected ParsedSentence, got {type(sentence).__name__}."
                )

            # 1. Inspect predicate subtree
            if 0 <= relation.predicate_index < sentence.token_count:
                pred_tok = sentence.get_token(relation.predicate_index)

                # Check predicate itself
                if (
                    pred_tok.lemma.lower() in self.NEGATION_LEMMAS
                    or "n't" in pred_tok.text.lower()
                    or pred_tok.text.lower() == "cannot"
                ):
                    negation_found.append(pred_tok.text)
                    evidence_notes.append(
                        f"Predicate token '{pred_tok.text}' is a negation marker."
                    )

                # Check direct children of predicate
                for child in sentence.get_children(pred_tok):
                    # Prepositions (e.g. "without") introduce adjuncts and must not negate the governing predicate
                    if child.dep in ("prep", "agent"):
                        continue

                    if (
                        child.dep == "neg"
                        or child.lemma.lower() in self.NEGATION_LEMMAS
                        or "n't" in child.text.lower()
                    ):
                        negation_found.append(child.text)
                        evidence_notes.append(
                            f"Negation marker '{child.text}' (dep={child.dep}) attached to predicate '{pred_tok.text}'."
                        )

                    # Check auxiliaries attached to predicate (e.g. does -> n't)
                    if child.dep in ("aux", "auxpass"):
                        for grand_child in sentence.get_children(child):
                            if (
                                grand_child.dep == "neg"
                                or grand_child.lemma.lower() in self.NEGATION_LEMMAS
                                or "n't" in grand_child.text.lower()
                            ):
                                negation_found.append(grand_child.text)
                                evidence_notes.append(
                                    f"Negation marker '{grand_child.text}' attached to auxiliary '{child.text}'."
                                )

            # 2. Inspect subject nominal determiners (e.g. "No key identifies...")
            if 0 <= relation.subject_index < sentence.token_count:
                subj_tok = sentence.get_token(relation.subject_index)
                for child in sentence.get_children(subj_tok):
                    if (
                        child.dep in ("det", "neg")
                        and child.lemma.lower() in ("no", "neither", "none")
                    ):
                        negation_found.append(child.text)
                        evidence_notes.append(
                            f"Negative determiner '{child.text}' modifying subject '{subj_tok.text}'."
                        )

            # 3. Inspect object nominal determiners (e.g. "...identifies no records")
            if (
                relation.object_index is not None
                and 0 <= relation.object_index < sentence.token_count
            ):
                obj_tok = sentence.get_token(relation.object_index)
                for child in sentence.get_children(obj_tok):
                    if (
                        child.dep in ("det", "neg")
                        and child.lemma.lower() in ("no", "neither", "none")
                    ):
                        negation_found.append(child.text)
                        evidence_notes.append(
                            f"Negative determiner '{child.text}' modifying object '{obj_tok.text}'."
                        )

        # Fallback / complementary lexical check on the relation strings
        pred_words = relation.predicate.lower().split()
        for w in pred_words:
            if w in self.NEGATION_LEMMAS or "n't" in w:
                if w not in negation_found:
                    negation_found.append(w)
                    evidence_notes.append(f"Lexical negation '{w}' in predicate surface text.")

        subj_words = relation.subject.lower().split()
        for w in subj_words:
            if w in ("no", "neither", "none", "not"):
                if w not in negation_found:
                    negation_found.append(w)
                    evidence_notes.append(f"Lexical negation '{w}' in subject surface text.")

        if relation.object:
            obj_words = relation.object.lower().split()
            for w in obj_words:
                if w in ("no", "neither", "none"):
                    if w not in negation_found:
                        negation_found.append(w)
                        evidence_notes.append(f"Lexical negation '{w}' in object surface text.")

        is_neg = len(negation_found) > 0
        polarity = "NEGATED" if is_neg else "POSITIVE"

        if is_neg:
            evidence_str = "; ".join(evidence_notes)
        else:
            evidence_str = "No negation markers detected; proposition has positive polarity."

        return PolarityInfo(
            polarity=polarity,
            is_negated=is_neg,
            negation_tokens=negation_found,
            evidence=evidence_str,
        )
