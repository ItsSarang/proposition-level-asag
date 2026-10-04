"""
Independent Unit Tests for Evidence Verification Layer (Phase 9).

Verifies:
1. Strict decoupling: Evidence verification operates independently from classification.
2. Positive verification of the 3 proof-of-architecture rules:
   - PK_NOT_NULL ("cannot contain NULL values")
   - BST_INORDER_SORTED ("inorder traversal yields sorted order")
   - COMPILER_INTERMEDIATE_REP ("generates an intermediate representation")
3. Polarity sensitivity:
   - "cannot contain NULL" -> SUPPORTED
   - "can contain NULL" -> NOT supported (UNVERIFIED)
4. Domain semantics:
   - Relevant != Supported: "requires an integer data type" -> UNVERIFIED
   - Absence from reference != Contradiction
   - WordNet similarity != Support
   - Domain lexicon equivalence != Support
5. Unknown concepts safely return UNVERIFIED.
6. Full provenance and academic citation preservation.
"""

import pytest

from base_asag.dependency.parser import DependencyParser
from base_asag.representation.hybrid import (
    Modality,
    Polarity,
    PropositionType,
    RobustProposition,
    RobustPropositionExtractor,
)
from proposed_asag.evidence.domain_knowledge import (
    CuratedDomainKnowledge,
    DomainPropertyRule,
)
from proposed_asag.evidence.evidence_verifier import (
    PropositionEvidenceVerifier,
)
from proposed_asag.evidence.models import (
    EvidenceSource,
    EvidenceStatus,
    VerificationEvidence,
)


@pytest.fixture(scope="module")
def parser():
    return DependencyParser()


@pytest.fixture(scope="module")
def extractor():
    return RobustPropositionExtractor()


@pytest.fixture(scope="module")
def verifier():
    return PropositionEvidenceVerifier()


def make_prop(
    subj,
    pred,
    obj,
    polarity=Polarity.POSITIVE,
    text="",
    properties=None,
):
    src = text or f"{subj} {pred} {obj}"
    return RobustProposition(
        subject=subj,
        predicate=pred,
        object=obj,
        subject_lemma=subj.lower() if subj else None,
        predicate_lemma=pred.lower() if pred else "",
        object_lemma=obj.lower() if obj else None,
        representation_type=PropositionType.TRIPLE,
        polarity=polarity,
        modality=Modality.ASSERTED,
        source_text=src,
        char_start=0,
        char_end=len(src),
        sentence_index=0,
        token_indices=(0, 1, 2),
        dependency_evidence=(),
        properties=properties or {},
    )


# 1. Proof of Architecture Rule: PK_NOT_NULL
def test_pk_not_null_positive_verification(parser, extractor, verifier):
    """'cannot contain NULL values' is verified by PK_NOT_NULL with correct negative polarity."""
    doc = parser.parse_document("A primary key cannot contain NULL values.")
    props = extractor.extract_document(doc)
    assert len(props) >= 1
    prop = props[0]

    evidence = verifier.verify(prop)
    assert isinstance(evidence, VerificationEvidence)
    assert evidence.status == EvidenceStatus.SUPPORTED
    assert evidence.source == EvidenceSource.DOMAIN_KNOWLEDGE_BASE
    assert evidence.rule_id == "PK_NOT_NULL"
    assert evidence.target_property == "nullability"
    assert "Silberschatz" in (evidence.academic_citation or "")
    assert evidence.confidence >= 0.85
    assert evidence.slot_matches["polarity"] == "NEGATIVE"


# 2. Polarity Sensitivity: False polarity must NOT match PK_NOT_NULL
def test_pk_polarity_sensitivity_positive_rejected(parser, extractor, verifier):
    """'can contain NULL values' (positive polarity) must NOT match PK_NOT_NULL."""
    doc = parser.parse_document("A primary key can contain NULL values.")
    props = extractor.extract_document(doc)
    assert len(props) >= 1
    prop = props[0]
    assert prop.polarity == Polarity.POSITIVE

    evidence = verifier.verify(prop)
    # Must NOT be supported
    assert evidence.status == EvidenceStatus.UNVERIFIED
    assert evidence.rule_id is None


# 3. Proof of Architecture Rule: BST_INORDER_SORTED
def test_bst_inorder_sorted_verification(parser, extractor, verifier):
    """'BST inorder traversal yields sorted order' is verified by BST_INORDER_SORTED."""
    prop = make_prop(
        subj="traversal",
        pred="yield",
        obj="order",
        polarity=Polarity.POSITIVE,
        text="BST inorder traversal yields sorted order",
    )
    evidence = verifier.verify(prop)
    assert evidence.status == EvidenceStatus.SUPPORTED
    assert evidence.rule_id == "BST_INORDER_SORTED"
    assert evidence.target_property == "ordering"
    assert "Cormen" in (evidence.academic_citation or "")
    assert evidence.confidence >= 0.85


# 4. Proof of Architecture Rule: COMPILER_INTERMEDIATE_REP
def test_compiler_intermediate_rep_verification(parser, extractor, verifier):
    """'compiler generates an intermediate representation' is verified by COMPILER_INTERMEDIATE_REP."""
    doc = parser.parse_document("A compiler generates an intermediate representation.")
    props = extractor.extract_document(doc)
    assert len(props) >= 1
    prop = props[0]

    evidence = verifier.verify(prop)
    assert evidence.status == EvidenceStatus.SUPPORTED
    assert evidence.rule_id == "COMPILER_INTERMEDIATE_REP"
    assert evidence.target_property == "intermediate_representation"
    assert "Aho" in (evidence.academic_citation or "")


# 5. Relevant != Supported: "requires an integer data type" is UNVERIFIED
def test_relevant_is_not_supported(verifier):
    """A domain-relevant proposition without an explicit supporting rule returns UNVERIFIED."""
    prop = make_prop(
        subj="key",
        pred="require",
        obj="type",
        polarity=Polarity.POSITIVE,
        text="primary key requires an integer data type",
    )
    evidence = verifier.verify(prop)
    assert evidence.status == EvidenceStatus.UNVERIFIED
    assert evidence.rule_id is None
    assert "UNVERIFIED" in evidence.rationale


# 6. Unknown Concept Safely Returns UNVERIFIED
def test_unknown_concept_unverified(verifier):
    """An unconfigured concept returns UNVERIFIED without errors."""
    prop = make_prop(
        subj="quicksort",
        pred="partition",
        obj="array",
        polarity=Polarity.POSITIVE,
        text="quicksort partitions an array around a pivot",
    )
    evidence = verifier.verify(prop)
    assert evidence.status == EvidenceStatus.UNVERIFIED
    assert evidence.rule_id is None


# 7. WordNet similarity is NOT Domain Verification
def test_wordnet_similarity_does_not_imply_verification(verifier):
    """
    High WordNet similarity between concepts does NOT constitute factual verification.
    The verifier only validates against explicit domain rules.
    """
    prop = make_prop(
        subj="key",
        pred="create",
        obj="identifier",
        polarity=Polarity.POSITIVE,
        text="primary key creates an identifier",
    )
    evidence = verifier.verify(prop)
    assert evidence.status == EvidenceStatus.UNVERIFIED


# 8. Domain Lexicon Equivalence is NOT Factual Verification
def test_domain_lexicon_does_not_imply_verification(verifier):
    """
    Knowing 'row' == 'record' does not verify arbitrary relational assertions about rows.
    """
    prop = make_prop(
        subj="row",
        pred="store",
        obj="memory",
        polarity=Polarity.POSITIVE,
        text="row stores memory",
    )
    evidence = verifier.verify(prop)
    assert evidence.status == EvidenceStatus.UNVERIFIED


# 9. Serialization of Verification Evidence
def test_verification_evidence_serialization(verifier):
    """VerificationEvidence serializes cleanly to dict."""
    prop = make_prop(
        subj="compiler",
        pred="generate",
        obj="representation",
        polarity=Polarity.POSITIVE,
        text="compiler generates intermediate representation",
    )
    evidence = verifier.verify(prop)
    d = evidence.to_dict()
    assert d["status"] == "SUPPORTED"
    assert d["rule_id"] == "COMPILER_INTERMEDIATE_REP"
    assert "Aho" in d["academic_citation"]
    assert isinstance(d["slot_matches"], dict)


# 10. End-to-End Classifier Integration for Controlled Cases
def test_classifier_integration_controlled_cases(parser, extractor):
    """
    Test all 5 controlled cases end-to-end through RobustAdditionalInfoClassifier:
    1. 'cannot contain NULL values' -> SUPPORTED -> CORRECT_ADDITIONAL
    2. 'requires an integer data type' -> UNVERIFIED -> UNCERTAIN
    3. 'can contain duplicate values' -> CONTRADICTED -> INCORRECT
    4. 'inorder traversal yields sorted order' -> SUPPORTED -> CORRECT_ADDITIONAL
    5. 'generates an intermediate representation' -> SUPPORTED -> CORRECT_ADDITIONAL
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()

    # Case 1: Primary Key + "cannot contain NULL values"
    q1 = "What is the purpose of a primary key?"
    r1 = "A primary key uniquely identifies each record in a table."
    ref1_props = extractor.extract_document(parser.parse_document(r1))

    s1_full = "A primary key uniquely identifies each record in a table and cannot contain NULL values."
    s1_props = extractor.extract_document(parser.parse_document(s1_full))
    s1_extra = s1_props[1]
    res1 = classifier.classify_propositions(q1, r1, s1_full, [s1_extra], reference_props=ref1_props)
    cp1 = res1.classified_propositions[0]
    assert cp1.classification == AdditionalInfoClass.CORRECT_ADDITIONAL
    assert cp1.verification_evidence.status == EvidenceStatus.SUPPORTED
    assert cp1.verification_evidence.rule_id == "PK_NOT_NULL"
    assert cp1.score_effect == 0.0

    # Case 2: Primary Key + "requires an integer data type"
    s2_full = "A primary key requires an integer data type."
    s2_extra = extractor.extract_document(parser.parse_document(s2_full))[0]
    res2 = classifier.classify_propositions(q1, r1, s2_full, [s2_extra], reference_props=ref1_props)
    cp2 = res2.classified_propositions[0]
    assert cp2.classification == AdditionalInfoClass.UNCERTAIN
    assert cp2.verification_evidence.status == EvidenceStatus.UNVERIFIED
    assert cp2.score_effect == 0.0

    # Case 3: Primary Key + "can contain duplicate values"
    s3_full = "A primary key uniquely identifies each record in a table and can contain duplicate values."
    s3_props = extractor.extract_document(parser.parse_document(s3_full))
    s3_extra = s3_props[1]
    res3 = classifier.classify_propositions(q1, r1, s3_full, [s3_extra], reference_props=ref1_props)
    cp3 = res3.classified_propositions[0]
    assert cp3.classification == AdditionalInfoClass.INCORRECT
    assert cp3.contradiction_evidence.is_contradicted is True
    assert cp3.verification_evidence.status == EvidenceStatus.CONTRADICTED

    # Case 4: BST + "inorder traversal yields sorted order"
    q4 = "What is a binary search tree?"
    r4 = "A binary search tree is a tree where the left child is smaller than the parent."
    ref4_props = extractor.extract_document(parser.parse_document(r4))
    s4_extra = make_prop("tree", "yield", "order", Polarity.POSITIVE, "binary search tree inorder traversal yields sorted order")
    res4 = classifier.classify_propositions(q4, r4, "binary search tree inorder traversal yields sorted order", [s4_extra], reference_props=ref4_props)
    cp4 = res4.classified_propositions[0]
    assert cp4.classification == AdditionalInfoClass.CORRECT_ADDITIONAL
    assert cp4.verification_evidence.status == EvidenceStatus.SUPPORTED
    assert cp4.verification_evidence.rule_id == "BST_INORDER_SORTED"

    # Case 5: Compiler + "generates an intermediate representation"
    q5 = "What does a compiler do?"
    r5 = "A compiler translates source code into machine code."
    ref5_props = extractor.extract_document(parser.parse_document(r5))
    s5_full = "A compiler translates source code and generates an intermediate representation."
    s5_props = extractor.extract_document(parser.parse_document(s5_full))
    s5_extra = s5_props[1]
    res5 = classifier.classify_propositions(q5, r5, s5_full, [s5_extra], reference_props=ref5_props)
    cp5 = res5.classified_propositions[0]
    assert cp5.classification == AdditionalInfoClass.CORRECT_ADDITIONAL
    assert cp5.verification_evidence.status == EvidenceStatus.SUPPORTED
    assert cp5.verification_evidence.rule_id == "COMPILER_INTERMEDIATE_REP"


# 11. Near-Miss and Polarity Variants
def test_near_miss_and_polarity_variants(parser, extractor):
    """
    Near-miss propositions must not trigger false positive support:
    - Preorder traversal does NOT yield sorted order (entity mismatch for sorted rule)
    - Positive polarity 'can contain NULL' does NOT match PK_NOT_NULL
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()
    q = "What is a binary search tree?"
    r = "A binary search tree is a tree where the left child is smaller than the parent."
    ref_props = extractor.extract_document(parser.parse_document(r))

    # Near-miss: "binary search tree preorder traversal yields sorted keys"
    preorder_prop = make_prop("tree", "yield", "key", Polarity.POSITIVE, "binary search tree preorder traversal yields sorted keys")
    res = classifier.classify_propositions(q, r, preorder_prop.source_text, [preorder_prop], reference_props=ref_props)
    cp = res.classified_propositions[0]
    # Entity 'preorder' is not 'inorder', so rule does not match
    assert cp.classification == AdditionalInfoClass.UNCERTAIN
    assert cp.verification_evidence.status == EvidenceStatus.UNVERIFIED


# 12. Regression Test A: Compiler Substring Leak
def test_compiler_substring_leak_regression(parser, extractor):
    """
    Ensure 'directly' never satisfies 'ir' through substring matching.
    Whole-token / whole-lemma matching must be strictly enforced.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()
    q = "What does a compiler do?"
    r = "A compiler translates source code into machine code."
    ref_props = extractor.extract_document(parser.parse_document(r))

    # 1. "A compiler generates an intermediate representation." -> SUPPORTED
    s1 = "A compiler generates an intermediate representation."
    p1 = extractor.extract_document(parser.parse_document(s1))
    res1 = classifier.classify_propositions(q, r, s1, p1, reference_props=ref_props)
    assert res1.classified_propositions[0].verification_evidence.status == EvidenceStatus.SUPPORTED

    # 2. "A compiler directly generates only source code." -> MUST NOT be SUPPORTED
    s2 = "A compiler directly generates only source code."
    p2 = extractor.extract_document(parser.parse_document(s2))
    res2 = classifier.classify_propositions(q, r, s2, p2, reference_props=ref_props)
    assert res2.classified_propositions[0].verification_evidence.status != EvidenceStatus.SUPPORTED
    assert res2.classified_propositions[0].classification != AdditionalInfoClass.CORRECT_ADDITIONAL

    # 3. "A compiler generates IR." -> SUPPORTED
    s3 = "A compiler generates IR."
    p3 = extractor.extract_document(parser.parse_document(s3))
    res3 = classifier.classify_propositions(q, r, s3, p3, reference_props=ref_props)
    assert res3.classified_propositions[0].verification_evidence.status == EvidenceStatus.SUPPORTED


# 13. Regression Test B: Primary-Key vs Foreign-Key Distinction
def test_primary_key_vs_foreign_key_distinction(parser, extractor):
    """
    Ensure PK_NOT_NULL distinguishes primary key from foreign key.
    Conflicting modifier 'foreign' must be explicitly rejected.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    ref_props = extractor.extract_document(parser.parse_document(r))

    # 1. "A primary key cannot contain NULL values." -> SUPPORTED
    s1 = "A primary key cannot contain NULL values."
    p1 = extractor.extract_document(parser.parse_document(s1))
    res1 = classifier.classify_propositions(q, r, s1, p1, reference_props=ref_props)
    assert res1.classified_propositions[0].verification_evidence.status == EvidenceStatus.SUPPORTED
    assert res1.classified_propositions[0].classification == AdditionalInfoClass.CORRECT_ADDITIONAL

    # 2. "Primary key attributes cannot contain NULL values." -> SUPPORTED
    s2 = "Primary key attributes cannot contain NULL values."
    p2 = extractor.extract_document(parser.parse_document(s2))
    res2 = classifier.classify_propositions(q, r, s2, p2, reference_props=ref_props)
    assert res2.classified_propositions[0].verification_evidence.status == EvidenceStatus.SUPPORTED
    assert res2.classified_propositions[0].classification == AdditionalInfoClass.CORRECT_ADDITIONAL

    # 3. "A foreign key cannot contain NULL values." -> MUST NOT be SUPPORTED
    s3 = "A foreign key cannot contain NULL values."
    p3 = extractor.extract_document(parser.parse_document(s3))
    res3 = classifier.classify_propositions(q, r, s3, p3, reference_props=ref_props)
    assert res3.classified_propositions[0].verification_evidence.status != EvidenceStatus.SUPPORTED
    assert res3.classified_propositions[0].classification != AdditionalInfoClass.CORRECT_ADDITIONAL

    # 4. "A foreign key can contain NULL values." -> MUST NOT be SUPPORTED
    s4 = "A foreign key can contain NULL values."
    p4 = extractor.extract_document(parser.parse_document(s4))
    res4 = classifier.classify_propositions(q, r, s4, p4, reference_props=ref_props)
    assert res4.classified_propositions[0].verification_evidence.status != EvidenceStatus.SUPPORTED


# 14. Regression Test C: Standalone 'Key' Does Not Imply Primary Key
def test_standalone_key_not_primary_key(parser, extractor):
    """
    A standalone 'key' lacks the required 'primary' modifier and must not receive PK_NOT_NULL support.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()
    q = "What is the purpose of a primary key?"
    r = "A primary key uniquely identifies each record in a table."
    ref_props = extractor.extract_document(parser.parse_document(r))

    s = "A key cannot contain NULL values."
    p = extractor.extract_document(parser.parse_document(s))
    res = classifier.classify_propositions(q, r, s, p, reference_props=ref_props)
    assert res.classified_propositions[0].verification_evidence.status != EvidenceStatus.SUPPORTED
    assert res.classified_propositions[0].classification != AdditionalInfoClass.CORRECT_ADDITIONAL


# 15. Regression Test D: BST Valid Additional Propositions Reach Evidence Layer
def test_bst_valid_additional_proposition_rescued(parser, extractor):
    """
    Legitimate BST propositions must be rescued from lexical overlap false negatives.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()
    q = "What is a binary search tree?"
    r = "A binary search tree is a tree where the left child is smaller than the parent."
    ref_props = extractor.extract_document(parser.parse_document(r))

    # BST_POS_1: "An inorder traversal of a BST produces sorted order."
    s1 = "An inorder traversal of a BST produces sorted order."
    p1 = extractor.extract_document(parser.parse_document(s1))
    res1 = classifier.classify_propositions(q, r, s1, p1, reference_props=ref_props)
    assert res1.classified_propositions[0].verification_evidence.status == EvidenceStatus.SUPPORTED
    assert res1.classified_propositions[0].classification == AdditionalInfoClass.CORRECT_ADDITIONAL
    assert res1.classified_propositions[0].verification_evidence.rule_id == "BST_INORDER_SORTED"

    # BST_POS_2: "A binary search tree's inorder traversal visits keys in ascending order."
    s2 = "A binary search tree's inorder traversal visits keys in ascending order."
    p2 = extractor.extract_document(parser.parse_document(s2))
    res2 = classifier.classify_propositions(q, r, s2, p2, reference_props=ref_props)
    assert res2.classified_propositions[0].verification_evidence.status == EvidenceStatus.SUPPORTED
    assert res2.classified_propositions[0].classification == AdditionalInfoClass.CORRECT_ADDITIONAL


# 16. Regression Test E: BST Preorder Adversarial Rejected
def test_bst_preorder_adversarial_rejected(parser, extractor):
    """
    Preorder traversal propositions must reach the verifier but be rejected.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()
    q = "What is a binary search tree?"
    r = "A binary search tree is a tree where the left child is smaller than the parent."
    ref_props = extractor.extract_document(parser.parse_document(r))

    for s in [
        "A preorder traversal of a BST produces sorted order.",
        "A BST's preorder traversal visits keys in ascending order.",
    ]:
        p = extractor.extract_document(parser.parse_document(s))
        res = classifier.classify_propositions(q, r, s, p, reference_props=ref_props)
        cp = res.classified_propositions[0]
        assert cp.verification_evidence.status != EvidenceStatus.SUPPORTED
        assert cp.classification != AdditionalInfoClass.CORRECT_ADDITIONAL


# 17. Regression Test F: General Binary Tree Proposition Rejected
def test_general_binary_tree_adversarial_rejected(parser, extractor):
    """
    'general binary tree' lacks the BST ordering property and must not receive BST_INORDER_SORTED support.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()
    q = "What is a binary search tree?"
    r = "A binary search tree is a tree where the left child is smaller than the parent."
    ref_props = extractor.extract_document(parser.parse_document(r))

    s = "Inorder traversal of a general binary tree always produces sorted order."
    p = extractor.extract_document(parser.parse_document(s))
    res = classifier.classify_propositions(q, r, s, p, reference_props=ref_props)
    cp = res.classified_propositions[0]
    assert cp.verification_evidence.status != EvidenceStatus.SUPPORTED
    assert cp.classification != AdditionalInfoClass.CORRECT_ADDITIONAL


# 18. Regression Test G: Interpreter Does Not Receive Compiler Support
def test_interpreter_adversarial_rejected(parser, extractor):
    """
    An interpreter is distinct from a compiler and must not receive COMPILER_INTERMEDIATE_REP support.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()
    q = "What does a compiler do?"
    r = "A compiler translates source code into machine code."
    ref_props = extractor.extract_document(parser.parse_document(r))

    s = "An interpreter generates an intermediate representation."
    p = extractor.extract_document(parser.parse_document(s))
    res = classifier.classify_propositions(q, r, s, p, reference_props=ref_props)
    cp = res.classified_propositions[0]
    assert cp.verification_evidence.status != EvidenceStatus.SUPPORTED
    assert cp.classification != AdditionalInfoClass.CORRECT_ADDITIONAL


# 19. Regression Test H: Existing Polarity Checks Continue Working
def test_polarity_adversarial_rejected(parser, extractor):
    """
    Negative polarity for compiler and positive polarity for primary key nullability must be rejected.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()

    # PK positive polarity
    q_pk = "What is the purpose of a primary key?"
    r_pk = "A primary key uniquely identifies each record in a table."
    ref_pk = extractor.extract_document(parser.parse_document(r_pk))
    s_pk = "A primary key can contain NULL values."
    p_pk = extractor.extract_document(parser.parse_document(s_pk))
    res_pk = classifier.classify_propositions(q_pk, r_pk, s_pk, p_pk, reference_props=ref_pk)
    assert res_pk.classified_propositions[0].verification_evidence.status != EvidenceStatus.SUPPORTED

    # Compiler negative polarity
    q_c = "What does a compiler do?"
    r_c = "A compiler translates source code into machine code."
    ref_c = extractor.extract_document(parser.parse_document(r_c))
    s_c = "A compiler never generates an intermediate representation."
    p_c = extractor.extract_document(parser.parse_document(s_c))
    res_c = classifier.classify_propositions(q_c, r_c, s_c, p_c, reference_props=ref_c)
    assert res_c.classified_propositions[0].verification_evidence.status != EvidenceStatus.SUPPORTED


# 20. Full 16-Case Controlled Robustness Validation Suite
def test_controlled_16_case_robustness_validation_suite(parser, extractor):
    """
    Executes the exact 16-case controlled robustness suite.
    Verifies that precision is 1.0 (zero false positive leaks on adversarial cases)
    and that all valid positive cases are supported.
    """
    from proposed_asag.classification.robust_classifier import (
        AdditionalInfoClass,
        RobustAdditionalInfoClassifier,
    )
    classifier = RobustAdditionalInfoClassifier()

    cases = [
        # PK Cases
        ("PK_POS_1", "What is the purpose of a primary key?", "A primary key uniquely identifies each record in a table.", "A primary key cannot contain NULL values.", True),
        ("PK_POS_2", "What is the purpose of a primary key?", "A primary key uniquely identifies each record in a table.", "Primary key attributes cannot contain NULL values.", True),
        ("PK_ADV_3", "What is the purpose of a primary key?", "A primary key uniquely identifies each record in a table.", "A primary key can contain NULL values.", False),
        ("PK_ADV_4", "What is the purpose of a primary key?", "A primary key uniquely identifies each record in a table.", "A foreign key cannot contain NULL values.", False),
        ("PK_ADV_5", "What is the purpose of a primary key?", "A primary key uniquely identifies each record in a table.", "A primary key does not require NULL values.", False),
        ("PK_ADV_6", "What is the purpose of a primary key?", "A primary key uniquely identifies each record in a table.", "NULL values are required for a primary key.", False),
        # BST Cases
        ("BST_POS_1", "What is a binary search tree?", "A binary search tree is a tree where the left child is smaller than the parent.", "An inorder traversal of a BST produces sorted order.", True),
        ("BST_POS_2", "What is a binary search tree?", "A binary search tree is a tree where the left child is smaller than the parent.", "A binary search tree's inorder traversal visits keys in ascending order.", True),
        ("BST_ADV_3", "What is a binary search tree?", "A binary search tree is a tree where the left child is smaller than the parent.", "A preorder traversal of a BST produces sorted order.", False),
        ("BST_ADV_4", "What is a binary search tree?", "A binary search tree is a tree where the left child is smaller than the parent.", "A BST's preorder traversal visits keys in ascending order.", False),
        ("BST_ADV_5", "What is a binary search tree?", "A binary search tree is a tree where the left child is smaller than the parent.", "Inorder traversal of a general binary tree always produces sorted order.", False),
        # Compiler Cases
        ("COMP_POS_1", "What does a compiler do?", "A compiler translates source code into machine code.", "A compiler generates an intermediate representation.", True),
        ("COMP_POS_2", "What does a compiler do?", "A compiler translates source code into machine code.", "Compilation may use an intermediate representation.", True),
        ("COMP_ADV_3", "What does a compiler do?", "A compiler translates source code into machine code.", "A compiler never generates an intermediate representation.", False),
        ("COMP_ADV_4", "What does a compiler do?", "A compiler translates source code into machine code.", "An interpreter generates an intermediate representation.", False),
        ("COMP_ADV_5", "What does a compiler do?", "A compiler translates source code into machine code.", "A compiler directly generates only source code.", False),
    ]

    tp = fp = fn = tn = 0
    for cid, q, r, s, exp_supp in cases:
        ref_props = extractor.extract_document(parser.parse_document(r))
        s_props = extractor.extract_document(parser.parse_document(s))
        res = classifier.classify_propositions(q, r, s, s_props, reference_props=ref_props)
        cp = res.classified_propositions[0]
        act_supp = (cp.verification_evidence.status == EvidenceStatus.SUPPORTED)

        if exp_supp and act_supp:
            tp += 1
        elif not exp_supp and not act_supp:
            tn += 1
        elif exp_supp and not act_supp:
            fn += 1
        else:
            fp += 1

    assert fp == 0, f"Critical leak: {fp} adversarial cases received SUPPORTED!"
    assert fn == 0, f"Gating defect: {fn} positive cases were not SUPPORTED!"
    assert tp == 6, f"Expected 6 TPs, got {tp}"
    assert tn == 10, f"Expected 10 TNs, got {tn}"
    precision = tp / (tp + fp)
    assert precision == 1.0

