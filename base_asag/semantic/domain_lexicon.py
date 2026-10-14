"""
Domain Lexicon and CS Equivalence Registry (Phase 3 & Controlled Audit).

Defines curated, auditable lexical equivalences commonly used in Computer Science
and programming education.

Design Principles:
1. Strict interpretability: Every equivalence is explicitly listed with domain justification.
2. No opaque embeddings: Equivalence is categorical and human-auditable.
3. Controlled toggle: Can be completely disabled via `use_domain_equivalence=False`.
4. Bidirectional mapping: Symmetric equivalence between technical terms.
"""

from typing import Dict, Optional, Set, Tuple

# Domain equivalence justification dictionary documenting linguistic and pedagogical rationale
DOMAIN_EQUIVALENCE_RATIONALE: Dict[str, str] = {
    "record": (
        "In databases and data structures, 'record', 'row', 'tuple', and 'entry' "
        "are standard synonyms denoting a single compound data item."
    ),
    "row": (
        "In relational databases and tabular structures, 'row' is synonymous with 'record' or 'tuple'."
    ),
    "convert": (
        "In compiler construction and type systems, 'convert', 'translate', 'transform', "
        "and 'cast' refer to mapping data or representations across formats."
    ),
    "translate": (
        "In compilation and interpretation, 'translate' and 'convert' refer to translating "
        "source code or intermediate representations."
    ),
    "instantiate": (
        "In object-oriented programming, 'instantiate', 'create', 'initialize', 'allocate', "
        "and 'construct' all refer to creating an object instance in memory."
    ),
    "create": (
        "In OOP, 'create' is commonly used by students to describe object instantiation or allocation."
    ),
    "prototype": (
        "In C/C++, a 'prototype' specifies the function 'declaration' or 'signature' before definition."
    ),
    "definition": (
        "In C/C++, a function 'definition' provides the 'implementation' and function 'body'."
    ),
    "terminate": (
        "In operating systems, recursion, and loops, 'terminate', 'stop', 'exit', 'finish', "
        "and 'halt' describe execution ending conditions."
    ),
    "deallocate": (
        "In manual memory management (C/C++), 'deallocate', 'free', 'release', and 'delete' "
        "refer to returning allocated heap memory."
    ),
    "free": (
        "In C memory management, 'free' is the standard operation to deallocate dynamic memory."
    ),
    "subroutine": (
        "In programming languages, 'subroutine', 'function', 'method', and 'procedure' "
        "are used interchangeably by introductory students to refer to callable code blocks."
    ),
    "function": (
        "In introductory CS, 'function', 'method', 'procedure', and 'subroutine' are "
        "frequently paired across procedural and object-oriented paradigms."
    ),
    "declare": (
        "In variable scoping and programming languages, 'declare' and 'define' are often "
        "used by students interchangeably to describe variable creation and specification in a block or function scope."
    ),
    "define": (
        "In programming languages and variable scoping, 'define' is used interchangeably "
        "with 'declare' regarding variable allocation and specification."
    ),
    "table": (
        "In relational databases, 'table' and 'relation' are standard technical synonyms "
        "originating from Codd's relational model."
    ),
    "relation": (
        "In relational database theory, 'relation' is the formal term for a tabular structure or 'table'."
    ),
    "column": (
        "In databases and tables, 'column', 'attribute', and 'field' denote vertical data dimensions."
    ),
    "attribute": (
        "In relational database theory and modeling, 'attribute' is synonymous with a table 'column' or 'field'."
    ),
    "pop": (
        "In stack data structures, 'pop' refers to removing the top element."
    ),
    "remove": (
        "In stack data structures, 'remove' describes the pop operation taking off the top element."
    ),
    "push": (
        "In stack data structures, 'push' refers to inserting or adding an element to the top."
    ),
    "insert": (
        "In stack data structures, 'insert' describes pushing or placing an element on top."
    ),
    "element": (
        "In data structures (arrays, stacks, lists), 'element' and 'item' refer to the constituent data members stored in the container."
    ),
    "item": (
        "In collections and data structures, 'item' is used synonymously with 'element' or 'entry'."
    ),
    "add": (
        "In collection operations (push, enqueue, append), 'add' describes inserting a new element."
    ),
}

# Curated Domain Lexical Equivalences
DOMAIN_LEXICAL_EQUIVALENCES: Dict[str, Set[str]] = {
    "record": {"row", "tuple", "entry"},
    "row": {"record", "tuple", "entry"},
    "convert": {"translate", "transform", "cast"},
    "translate": {"convert", "transform"},
    "instantiate": {"create", "initialize", "allocate", "construct"},
    "create": {"instantiate", "construct"},
    "prototype": {"declaration", "signature"},
    "definition": {"implementation", "body"},
    "terminate": {"stop", "exit", "finish", "halt"},
    "deallocate": {"free", "release", "delete"},
    "free": {"deallocate", "release"},
    "subroutine": {"function", "method", "procedure"},
    "function": {"subroutine", "method", "procedure"},
    "declare": {"define"},
    "define": {"declare"},
    "table": {"relation"},
    "relation": {"table"},
    "column": {"attribute", "field"},
    "attribute": {"column", "field"},
    "pop": {"remove"},
    "remove": {"pop"},
    "push": {"insert", "add"},
    "insert": {"push", "add"},
    "add": {"push", "insert"},
    "element": {"item"},
    "item": {"element"},
}


def are_domain_equivalent(term1: str, term2: str) -> bool:
    """
    Check whether two terms are considered equivalent under the domain lexicon.
    Case-insensitive lemma-level comparison.
    """
    t1 = term1.strip().lower()
    t2 = term2.strip().lower()
    if t1 == t2:
        return True
    if t1 in DOMAIN_LEXICAL_EQUIVALENCES:
        return t2 in DOMAIN_LEXICAL_EQUIVALENCES[t1]
    return False


def get_domain_equivalence_rationale(term: str) -> Optional[str]:
    """Retrieve the documented CS rationale for a term's domain equivalence."""
    return DOMAIN_EQUIVALENCE_RATIONALE.get(term.strip().lower())
