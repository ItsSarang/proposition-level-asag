"""
Controlled Repair Regression Tests: Bug 1 (Antonym Contradiction) & Bug 2 (BST Overgeneralization).

Explicitly validates Cases A through I from the Controlled Development Repair phase:
- Case A: Correct LIFO answer -> MUST NOT produce contradiction
- Case B: Genuine FIFO/LIFO contradiction -> SHOULD be detected
- Case C: Genuine first/last contradiction -> SHOULD be detected
- Case D: Correct BST inorder sorted statement -> SUPPORTED
- Case E: General binary-tree inorder sorted statement -> MUST NOT be SUPPORTED
- Case F: Preorder BST sorted statement -> MUST NOT be SUPPORTED
- Case G: Interpreter/compiler entity mismatch -> MUST remain rejected
- Case H: Foreign-key/primary-key distinction -> MUST remain rejected correctly
- Case I: Compiler 'directly' / 'IR' substring regression -> MUST remain rejected correctly
"""

import pytest
from base_asag.dependency.parser import DependencyParser
from base_asag.representation.hybrid import RobustPropositionExtractor, Polarity
from proposed_asag.evidence.evidence_verifier import PropositionEvidenceVerifier, EvidenceStatus
from proposed_asag.contradiction.property_contradiction import PropertyContradictionDetector, ContradictionType
from proposed_asag.classification.robust_classifier import RobustAdditionalInfoClassifier, AdditionalInfoClass
from proposed_asag.overhauled_pipeline import OverhauledASAGPipeline


@pytest.fixture(scope="module")
def parser():
    return DependencyParser()


@pytest.fixture(scope="module")
def extractor():
    return RobustPropositionExtractor()


@pytest.fixture(scope="module")
def verifier():
    return PropositionEvidenceVerifier()


@pytest.fixture(scope="module")
def detector():
    return PropertyContradictionDetector()


@pytest.fixture(scope="module")
def pipeline():
    return OverhauledASAGPipeline()


# =====================================================================
# Case A: Correct LIFO Answer (Bug 1 Known Failure Q8.1 S5)
# =====================================================================
def test_case_a_correct_lifo_no_contradiction(pipeline, detector, parser, extractor):
    """
    Case A: Correct LIFO answer against reference with 'last ... first ... removed'.
    MUST NOT produce contradiction or negative adjustment.
    """
    q = "What is a stack?"
    ref = (
        "A data structure that can store elements, which has the property that "
        "the last item added will be the first to be removed (or last-in-first-out)"
    )
    stu = (
        "a stack is a data structure that uses push to insert an item and pop "
        "to remove ad item. The stack use a last in first out structure for "
        "inserting and removing items."
    )

    # Full pipeline check
    res = pipeline.evaluate(q, ref, stu)
    assert res.incorrect_count == 0, f"Expected 0 incorrect propositions, got {res.incorrect_count}"
    assert res.negative_adjustment == 0.0, f"Expected 0.0 negative adjustment, got {res.negative_adjustment}"

    # Proposition-level contradiction check
    ref_props = extractor.extract_document(parser.parse_document(ref))
    stu_props = extractor.extract_document(parser.parse_document(stu))
    for p in stu_props:
        ev = detector.detect_contradiction(p, ref_props)
        assert ev.is_contradicted is False, f"False contradiction detected on: '{p.source_text}': {ev.explanation}"


# =====================================================================
# Case B: Genuine FIFO/LIFO Contradiction
# =====================================================================
def test_case_b_genuine_fifo_lifo_contradiction(pipeline, detector, parser, extractor):
    """
    Case B: Genuine FIFO/LIFO contradiction.
    A stack described as FIFO when reference specifies LIFO MUST be detected as contradiction.
    """
    q = "What is a stack?"
    ref = (
        "A data structure that can store elements, which has the property that "
        "the last item added will be the first to be removed (or last-in-first-out)"
    )
    stu = "A stack is a data structure that uses first in first out order to store elements."

    # Full pipeline check
    res = pipeline.evaluate(q, ref, stu)
    assert res.incorrect_count >= 1, f"Expected at least 1 incorrect proposition, got {res.incorrect_count}"
    assert res.negative_adjustment > 0.0, f"Expected negative penalty, got {res.negative_adjustment}"

    # Detector-level value conflict check
    ref_props = extractor.extract_document(parser.parse_document(ref))
    stu_props = extractor.extract_document(parser.parse_document(stu))

    contradictions = [detector.detect_contradiction(p, ref_props) for p in stu_props]
    detected = [c for c in contradictions if c.is_contradicted]
    assert len(detected) >= 1, "Expected contradiction evidence on FIFO vs LIFO"
    val_conflicts = [c for c in detected if c.contradiction_type == ContradictionType.VALUE_CONFLICT]
    assert len(val_conflicts) >= 1, "Expected VALUE_CONFLICT contradiction type"
    assert val_conflicts[0].conflicting_property == "access_discipline"


# =====================================================================
# Case C: Genuine First/Last Predicate Contradiction
# =====================================================================
def test_case_c_genuine_first_last_contradiction(detector, parser, extractor):
    """
    Case C: Genuine first/last contradiction on matching predicate.
    'The first item is removed last' vs 'The first item is removed first'
    MUST be detected as an antonym contradiction.
    """
    ref_text = "The first item is removed first."
    stu_text = "The first item is removed last."

    ref_props = extractor.extract_document(parser.parse_document(ref_text))
    stu_props = extractor.extract_document(parser.parse_document(stu_text))

    assert len(stu_props) >= 1
    assert len(ref_props) >= 1

    ev = detector.detect_contradiction(stu_props[0], ref_props)
    assert ev.is_contradicted is True, "Expected contradiction between 'removed last' and 'removed first'"
    assert ev.contradiction_type == ContradictionType.ANTONYM_CONFLICT
    assert "antonym" in ev.explanation.lower()


# =====================================================================
# Case D: Correct BST Inorder Sorted Statement
# =====================================================================
@pytest.mark.parametrize(
    "stu_sentence",
    [
        "An inorder traversal of a BST produces sorted order.",
        "A binary search tree's inorder traversal visits keys in ascending order.",
        "BST inorder traversal yields sorted order.",
    ],
)
def test_case_d_correct_bst_inorder_sorted(stu_sentence, verifier, parser, extractor):
    """
    Case D: Valid BST inorder statements explicitly identifying BST/search tree
    MUST be verified as SUPPORTED by BST_INORDER_SORTED.
    """
    doc = parser.parse_document(stu_sentence)
    props = extractor.extract_document(doc, stu_sentence)
    assert len(props) >= 1
    ev = verifier.verify(props[0])
    assert ev.status == EvidenceStatus.SUPPORTED
    assert ev.rule_id == "BST_INORDER_SORTED"
    assert ev.target_property == "ordering"


# =====================================================================
# Case E: General Binary Tree Inorder Statement (Bug 2 Known Failure Q10.6 S1)
# =====================================================================
@pytest.mark.parametrize(
    "stu_sentence",
    [
        "The inorder traversal of a binary tree visits the node of a binary tree in order according to their data values.",
        "Inorder traversal of a binary tree produces sorted order.",
        "A general binary tree's inorder traversal yields sorted keys.",
        "Inorder traversal of a tree produces sorted order.",
    ],
)
def test_case_e_general_binary_tree_must_not_be_supported(stu_sentence, verifier, parser, extractor):
    """
    Case E: General binary tree statements lacking explicit BST/search-tree concepts
    MUST NOT be SUPPORTED (held as UNVERIFIED).
    """
    doc = parser.parse_document(stu_sentence)
    props = extractor.extract_document(doc, stu_sentence)
    assert len(props) >= 1
    ev = verifier.verify(props[0])
    assert ev.status != EvidenceStatus.SUPPORTED, f"Expected non-SUPPORTED for general binary tree: '{stu_sentence}'"
    assert ev.rule_id is None


# =====================================================================
# Case F: Preorder BST Statement
# =====================================================================
@pytest.mark.parametrize(
    "stu_sentence",
    [
        "A preorder traversal of a BST produces sorted order.",
        "A BST's preorder traversal visits keys in ascending order.",
    ],
)
def test_case_f_preorder_bst_must_not_be_supported(stu_sentence, verifier, parser, extractor):
    """
    Case F: Preorder traversals of BST do not yield sorted order and MUST NOT be SUPPORTED.
    """
    doc = parser.parse_document(stu_sentence)
    props = extractor.extract_document(doc, stu_sentence)
    assert len(props) >= 1
    ev = verifier.verify(props[0])
    assert ev.status != EvidenceStatus.SUPPORTED
    assert ev.rule_id is None


# =====================================================================
# Case G: Interpreter / Compiler Entity Mismatch
# =====================================================================
def test_case_g_interpreter_compiler_mismatch_rejected(verifier, parser, extractor):
    """
    Case G: An interpreter is distinct from a compiler and MUST NOT receive COMPILER_INTERMEDIATE_REP support.
    """
    s = "An interpreter generates an intermediate representation."
    doc = parser.parse_document(s)
    props = extractor.extract_document(doc, s)
    assert len(props) >= 1
    ev = verifier.verify(props[0])
    assert ev.status != EvidenceStatus.SUPPORTED
    assert ev.rule_id is None


# =====================================================================
# Case H: Foreign Key / Primary Key Distinction
# =====================================================================
def test_case_h_foreign_key_rejected(verifier, parser, extractor):
    """
    Case H: Foreign keys can contain NULLs and MUST NOT receive PK_NOT_NULL support.
    """
    s = "A foreign key cannot contain NULL values."
    doc = parser.parse_document(s)
    props = extractor.extract_document(doc, s)
    assert len(props) >= 1
    ev = verifier.verify(props[0])
    assert ev.status != EvidenceStatus.SUPPORTED
    assert ev.rule_id is None


# =====================================================================
# Case I: Compiler "directly" / "IR" Substring Regression
# =====================================================================
def test_case_i_compiler_directly_substring_leak_rejected(verifier, parser, extractor):
    """
    Case I: 'directly' contains 'ir' as a substring. Whole-token matching
    MUST ensure this proposition is NOT mistakenly SUPPORTED.
    """
    s = "A compiler directly generates only source code."
    doc = parser.parse_document(s)
    props = extractor.extract_document(doc, s)
    assert len(props) >= 1
    ev = verifier.verify(props[0])
    assert ev.status != EvidenceStatus.SUPPORTED
    assert ev.rule_id is None
