# Research Methodology

The project implements a 6-stage methodological progression:
1. **Linguistic Preprocessing**: Tokenization, lemmatization, POS tagging via spaCy.
2. **Proposition Extraction**: Clausal Subject-Predicate-Object triples and hybrid relational units.
3. **Semantic Matching**: Exact, lemma, POS compatibility, WordNet synset similarity, and domain equivalences.
4. **Textual Entailment**: Polarity checking, negation scope detection, and candidate alignment.
5. **Proposition-Level Extension**: Extraction and classification of unmatched student propositions.
6. **Interpretability & Scoring**: Additive, bounded, and severity-aware scoring functions preserving exact audit traces.
