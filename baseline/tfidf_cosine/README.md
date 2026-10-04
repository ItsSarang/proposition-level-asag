# TF-IDF + Cosine Similarity Baseline

This directory contains the implementation of **System 1: Simple Baseline**, a classical surface-level similarity benchmark for Automated Short Answer Grading (ASAG).

---

## 1. What TF-IDF Is

**Term Frequency-Inverse Document Frequency (TF-IDF)** is a statistical measure that quantifies the relative importance of words within a document across a collection of texts:

- **Term Frequency (TF):** Measures how frequently a word appears in a specific document.
- **Inverse Document Frequency (IDF):** Penalizes words that appear ubiquitously across many documents (such as common function words) and boosts unique, content-bearing terms.

In this baseline pairwise formulation, texts are represented as sparse numerical vectors where each dimension corresponds to a vocabulary term weighted by its TF-IDF score.

---

## 2. What Cosine Similarity Is

**Cosine Similarity** measures the angle between two multi-dimensional vectors in a vector space, defined as:

$$\text{Cosine Similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|}$$

- If two texts share identical word distributions, the angle is $0^\circ$ and cosine similarity is **1.0**.
- If two texts share no common terms, the vectors are orthogonal and cosine similarity is **0.0**.
- Scores naturally range between **0.0 and 1.0** for non-negative TF-IDF representations.

---

## 3. Why This Is Used as a Baseline

In ASAG research, a surface-level lexical similarity baseline serves two vital methodological functions:

1. **Lower-Bound Benchmark:** Establishes the simplest statistical baseline that requires zero linguistic parsing, semantic knowledge, or domain-specific rule engineering.
2. **Evaluation Reference:** Any proposed semantic or dependency-based ASAG pipeline (such as the Basak-inspired Base ASAG or the proposed proposition-level extension) must demonstrate clear, empirical advantages over this baseline to justify added complexity.

---

## 4. What the Baseline Can Capture

- **Exact Word Matches:** Accurately recognizes shared terminology and key domain concepts.
- **Word Frequency Overlap:** Weighs repeated and salient shared vocabulary higher than single-occurrence terms.
- **Surface Lexical Relevance:** Effectively separates answers with high verbatim overlap from completely unrelated responses.

---

## 5. What the Baseline Cannot Capture

- **Paraphrasing and Synonyms:** Cannot recognize that "uniquely identifies every row" conveys the same concept as "uniquely identifies each record".
- **Syntactic Structure and Dependency:** Ignores word order and grammatical roles (e.g., "dog bit man" vs. "man bit dog" appear identical under bag-of-words).
- **Negation and Polarity:** Fails to discern polarity changes (e.g., "can contain NULLs" vs. "cannot contain NULLs" receive very high lexical similarity despite opposite meanings).
- **Extra or Misconception Information:** Cannot differentiate whether extra words represent correct elaboration, irrelevant remarks, or factual misconceptions.

---

## 6. Lexical Baseline Status

This module is strictly a **lexical similarity baseline**. It does not perform semantic reasoning, dependency parsing, textual entailment, or proposition decomposition. It outputs a continuous similarity metric $[0.0, 1.0]$, not a definitive grading decision or rubric score.
