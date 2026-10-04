"""
Curated Domain Knowledge Registry (Phase 9).

Defines explicit, auditable Computer Science property rules for verifying
unmatched student propositions, strictly decoupled from grading classifiers.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from base_asag.representation.hybrid import Polarity, RobustProposition


@dataclass(frozen=True)
class DomainPropertyRule:
    """
    An explicit, auditable factual property rule in Computer Science.
    Supports entity modifier constraints and domain topic associations.
    """
    rule_id: str
    target_entity_lemmas: Tuple[str, ...]
    predicate_lemmas: Tuple[str, ...]
    object_lemmas: Tuple[str, ...]
    required_polarity: Polarity
    property_category: str
    rationale: str
    academic_citation: str
    required_entity_modifiers: Tuple[str, ...] = ()
    forbidden_entity_modifiers: Tuple[str, ...] = ()
    domain_topic_lemmas: Tuple[str, ...] = ()
    required_concept_groups: Tuple[Tuple[str, ...], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "rule_id": self.rule_id,
            "target_entity_lemmas": list(self.target_entity_lemmas),
            "predicate_lemmas": list(self.predicate_lemmas),
            "object_lemmas": list(self.object_lemmas),
            "required_polarity": self.required_polarity.value,
            "property_category": self.property_category,
            "rationale": self.rationale,
            "academic_citation": self.academic_citation,
            "required_entity_modifiers": list(self.required_entity_modifiers),
            "forbidden_entity_modifiers": list(self.forbidden_entity_modifiers),
            "domain_topic_lemmas": list(self.domain_topic_lemmas),
        }
        if self.required_concept_groups:
            d["required_concept_groups"] = [list(g) for g in self.required_concept_groups]
        return d


class CuratedDomainKnowledge:
    """
    Curated repository of auditable CS domain rules.
    Contains strictly the 3 proof-of-architecture rules with explicit
    modifier constraints and whole-token matching to eliminate substring/keyword leaks.
    """

    DEFAULT_RULES: Tuple[DomainPropertyRule, ...] = (
        DomainPropertyRule(
            rule_id="PK_NOT_NULL",
            target_entity_lemmas=("key", "primary", "attribute", "column"),
            predicate_lemmas=("contain", "have", "allow", "accept", "permit", "admit", "be"),
            object_lemmas=("null", "nil", "empty"),
            required_polarity=Polarity.NEGATIVE,
            property_category="nullability",
            rationale="Primary key attributes cannot contain NULL values to enforce entity integrity in relational databases.",
            academic_citation="Silberschatz, A., Korth, H. F., & Sudarshan, S. (2019). Database System Concepts (7th ed.). McGraw-Hill, Section 2.3.",
            required_entity_modifiers=("primary",),
            forbidden_entity_modifiers=("foreign", "candidate", "alternate", "surrogate"),
            domain_topic_lemmas=("primary", "key", "table", "relational", "database", "record"),
        ),
        DomainPropertyRule(
            rule_id="BST_INORDER_SORTED",
            target_entity_lemmas=("inorder", "traversal", "bst", "tree"),
            predicate_lemmas=("yield", "produce", "traverse", "give", "result", "visit", "sort", "output"),
            object_lemmas=("sort", "order", "sorted", "ascending"),
            required_polarity=Polarity.POSITIVE,
            property_category="ordering",
            rationale="An inorder tree traversal of a binary search tree visits nodes and outputs keys in ascending sorted order.",
            academic_citation="Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2009). Introduction to Algorithms (3rd ed.). MIT Press, Theorem 12.1.",
            required_entity_modifiers=("inorder",),
            forbidden_entity_modifiers=("preorder", "postorder", "levelorder", "general"),
            domain_topic_lemmas=("bst", "binary", "tree", "traversal", "inorder", "node", "search"),
            required_concept_groups=(("inorder",), ("bst", "search")),
        ),
        DomainPropertyRule(
            rule_id="COMPILER_INTERMEDIATE_REP",
            target_entity_lemmas=("compiler", "compilation", "translation"),
            predicate_lemmas=("generate", "produce", "emit", "create", "use", "translate"),
            object_lemmas=("intermediate", "ir", "bytecode"),
            required_polarity=Polarity.POSITIVE,
            property_category="intermediate_representation",
            rationale="Compilers typically translate source code into an intermediate representation (IR) prior to target machine code generation.",
            academic_citation="Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006). Compilers: Principles, Techniques, and Tools (2nd ed.). Addison-Wesley, Section 1.2.",
            required_entity_modifiers=(),
            forbidden_entity_modifiers=("interpreter", "assembler"),
            domain_topic_lemmas=("compiler", "compilation", "intermediate", "ir", "code", "translate"),
        ),
    )

    def __init__(self, rules: Optional[Sequence[DomainPropertyRule]] = None) -> None:
        self._rules: Tuple[DomainPropertyRule, ...] = tuple(rules) if rules is not None else self.DEFAULT_RULES
        self._rule_lookup: Dict[str, DomainPropertyRule] = {r.rule_id: r for r in self._rules}

    def get_rule(self, rule_id: str) -> Optional[DomainPropertyRule]:
        """Retrieve a rule by its unique identifier."""
        return self._rule_lookup.get(rule_id)

    def all_rules(self) -> Tuple[DomainPropertyRule, ...]:
        """Return all registered domain rules."""
        return self._rules

    def find_matching_rule(
        self, proposition: RobustProposition
    ) -> Optional[Tuple[DomainPropertyRule, Dict[str, Any]]]:
        """
        Evaluate proposition against curated rules.
        Returns the matching rule and matched slot evidence, or None.

        Epistemic constraints:
        1. Polarity matching: Required polarity must match proposition polarity.
        2. Whole-token matching: Strictly avoids unconstrained substring matches (e.g. 'ir' in 'directly').
        3. Forbidden entity modifiers: Conflicting concepts (e.g. 'foreign' for PK, 'preorder' for BST) are rejected.
        4. Required entity modifiers: Specialized entities (e.g. 'primary' for PK) must be present.
        """
        # 1. Collect entity tokens/lemmas
        subj_tokens: Set[str] = set()
        if proposition.subject_lemma:
            subj_tokens.add(proposition.subject_lemma.lower())
        if proposition.subject:
            subj_tokens.update(re.findall(r"\b[A-Za-z0-9_]+\b", proposition.subject.lower()))
        if "subject_tree_lemmas" in proposition.properties:
            subj_tokens.update(t.lower() for t in proposition.properties["subject_tree_lemmas"])

        # Also extract pre-predicate tokens from source_text if available
        if proposition.source_text and proposition.predicate:
            pred_idx = proposition.source_text.lower().find(proposition.predicate.lower())
            if pred_idx > 0:
                subj_tokens.update(re.findall(r"\b[A-Za-z0-9_]+\b", proposition.source_text[:pred_idx].lower()))
            elif pred_idx == -1 and proposition.predicate_lemma:
                pred_idx_lem = proposition.source_text.lower().find(proposition.predicate_lemma.lower())
                if pred_idx_lem > 0:
                    subj_tokens.update(re.findall(r"\b[A-Za-z0-9_]+\b", proposition.source_text[:pred_idx_lem].lower()))

        # 2. Collect predicate tokens/lemmas
        pred_tokens: Set[str] = set()
        if proposition.predicate_lemma:
            pred_tokens.add(proposition.predicate_lemma.lower())
        if proposition.predicate:
            pred_tokens.update(re.findall(r"\b[A-Za-z0-9_]+\b", proposition.predicate.lower()))

        # 3. Collect object tokens/lemmas (whole-token only)
        obj_tokens: Set[str] = set()
        if proposition.object_lemma:
            obj_tokens.add(proposition.object_lemma.lower())
        if proposition.object:
            obj_tokens.update(re.findall(r"\b[A-Za-z0-9_]+\b", proposition.object.lower()))
        if "object_tree_lemmas" in proposition.properties:
            obj_tokens.update(t.lower() for t in proposition.properties["object_tree_lemmas"])
        if "prep_phrase_lemmas" in proposition.properties:
            obj_tokens.update(t.lower() for t in proposition.properties["prep_phrase_lemmas"])

        # Post-predicate tokens from source_text
        if proposition.source_text and proposition.predicate:
            pred_idx = proposition.source_text.lower().find(proposition.predicate.lower())
            if pred_idx >= 0:
                post_text = proposition.source_text[pred_idx + len(proposition.predicate):].lower()
                obj_tokens.update(re.findall(r"\b[A-Za-z0-9_]+\b", post_text))
            elif proposition.predicate_lemma:
                pred_idx_lem = proposition.source_text.lower().find(proposition.predicate_lemma.lower())
                if pred_idx_lem >= 0:
                    post_text = proposition.source_text[pred_idx_lem + len(proposition.predicate_lemma):].lower()
                    obj_tokens.update(re.findall(r"\b[A-Za-z0-9_]+\b", post_text))

        for rule in self._rules:
            # Step A: Polarity check (must match required polarity exactly)
            if proposition.polarity != rule.required_polarity:
                continue

            # Step B: Forbidden entity modifiers check (reject immediately if conflicting modifier present)
            forbidden_found = [m for m in rule.forbidden_entity_modifiers if m in subj_tokens]
            if forbidden_found:
                continue

            # Step C: Target entity check (whole-token match against target_entity_lemmas)
            entity_matches = [e for e in rule.target_entity_lemmas if e in subj_tokens]
            if not entity_matches:
                continue

            # Step D1: Required entity modifiers check (e.g. 'primary' for PK_NOT_NULL)
            if rule.required_entity_modifiers:
                req_found = [m for m in rule.required_entity_modifiers if m in subj_tokens]
                if not req_found:
                    continue

            # Step D2: Required concept groups check (each group must have at least one token present)
            if rule.required_concept_groups:
                all_groups_present = all(
                    any(c in subj_tokens for c in group)
                    for group in rule.required_concept_groups
                )
                if not all_groups_present:
                    continue

            # Step E: Predicate check (whole-token match against predicate_lemmas)
            pred_matches = [p for p in rule.predicate_lemmas if p in pred_tokens]
            if not pred_matches:
                continue

            # Step F: Object check (whole-token match against object_lemmas)
            obj_matches = [o for o in rule.object_lemmas if o in obj_tokens]
            if not obj_matches:
                continue

            # Matched!
            slot_evidence = {
                "entity_matches": sorted(list(set(entity_matches))),
                "predicate_matches": sorted(list(set(pred_matches))),
                "object_matches": sorted(list(set(obj_matches))),
                "polarity": proposition.polarity.value,
            }
            return rule, slot_evidence

        return None

    def is_domain_applicable(
        self,
        proposition: RobustProposition,
        question: str = "",
        reference_answer: str = "",
    ) -> bool:
        """
        Check if an unmatched proposition is domain-applicable to a curated rule
        in the context of the question and reference answer.
        Rescues domain-relevant propositions from lexical question-overlap false negatives.
        """
        # If the proposition directly satisfies a rule, it is inherently applicable
        if self.find_matching_rule(proposition) is not None:
            return True

        context_text = f"{question} {reference_answer}".lower()
        context_tokens = set(re.findall(r"\b[A-Za-z0-9_]+\b", context_text))

        prop_tokens: Set[str] = set()
        if proposition.source_text:
            prop_tokens.update(re.findall(r"\b[A-Za-z0-9_]+\b", proposition.source_text.lower()))
        if proposition.subject_lemma:
            prop_tokens.add(proposition.subject_lemma.lower())
        if proposition.predicate_lemma:
            prop_tokens.add(proposition.predicate_lemma.lower())
        if proposition.object_lemma:
            prop_tokens.add(proposition.object_lemma.lower())
        if "subject_tree_lemmas" in proposition.properties:
            prop_tokens.update(t.lower() for t in proposition.properties["subject_tree_lemmas"])
        if "object_tree_lemmas" in proposition.properties:
            prop_tokens.update(t.lower() for t in proposition.properties["object_tree_lemmas"])
        if "prep_phrase_lemmas" in proposition.properties:
            prop_tokens.update(t.lower() for t in proposition.properties["prep_phrase_lemmas"])

        for rule in self._rules:
            # 1. Does the assessment question/reference connect to this rule domain?
            topic_set = set(rule.domain_topic_lemmas)
            context_overlap = context_tokens.intersection(topic_set)
            if not context_overlap:
                continue

            # 2. Does the student proposition connect to this rule domain or entity?
            rule_domain_and_entities = topic_set.union(rule.target_entity_lemmas)
            prop_overlap = prop_tokens.intersection(rule_domain_and_entities)
            if prop_overlap:
                return True

        return False
