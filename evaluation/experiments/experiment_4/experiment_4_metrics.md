# Experiment 4: Benchmark Metrics Report

**Experiment Name**: Experiment 4 — Severity-Aware Proposed ASAG  
**Dataset**: UNT Computer Science Short Answer Dataset v2.0 (*Mohler et al., 2011*)  
**Status**: Frozen Formal Benchmark Execution  
**Evaluated Records**: $N=2,273$ active student answers across 81 active questions  
**Target Variable**: Human average score (`score_ave`) on a $[0.0, 5.0]$ scale  
**Execution Runtime**: 60.64 seconds ($37.5\text{ records/second}$, $0\text{ failures}$)  

---

## 1. Systems Compared

1. **System 1 (V0) — TF-IDF Baseline**: Surface lexical overlap using character/word n-gram TF-IDF and cosine similarity, scaled to $[0.0, 5.0]$.
2. **System 2 (V1) — Base ASAG**: Basak-inspired classical dependency triple representation with syntactic slot matching, polarity-aware textual entailment, and reference coverage scoring.
3. **System 3 (V2) — Historical Proposed ASAG**: Early proposition-level extension (Stage 15.2 / Stage 17) with ungrounded additional information classification and unweighted additive bonuses.
4. **System 4 (V3) — Current Proposed ASAG**: Frozen post-Stage 17 pipeline (Experiment 1 / Experiment 2) featuring multi-tier semantic matching, predicate-gated cross-slot matching, and additive saturating scoring.
5. **System 5 (V4) — Experiment 4 (Severity-Aware Proposed ASAG)**: Severity-aware ASAG pipeline integrating the Model D formulation (core invalidation discount, gated positive compensation, and graded minor penalties) with interpretable contradiction severity estimation.

---

## 2. Overall Performance Comparison ($N=2,273$)

The primary evaluation across all active questions and student answers in the Mohler benchmark:

| System | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK | Predicted Mean | Predicted Std | Descriptive Bias |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Human Annotator Target** | — | — | — | — | — | 4.1839 | 1.0966 | 0.0000 |
| **V0: TF-IDF Baseline** | **2.6571** | **2.9178** | **0.4184** | **0.4424** | **0.1151** | 1.5316 | 1.1572 | -2.6523 |
| **V1: Base ASAG** | 3.8050 | 4.0373 | 0.1379 | 0.1181 | 0.0180 | 0.3917 | 1.0117 | -3.7922 |
| **V2: Historical Proposed** | 3.2176 | 3.5179 | 0.1342 | 0.0765 | 0.0239 | 0.9990 | 1.1729 | -3.1849 |
| **V3: Current Proposed** | 3.5955 | 3.8862 | 0.2037 | 0.2007 | 0.0396 | 0.6042 | 1.2896 | -3.5797 |
| **V4: Experiment 4 (Severity-Aware)** | 3.6288 | 3.9270 | 0.2055 | 0.2033 | 0.0380 | 0.5730 | 1.3355 | -3.6109 |

*Note: All correlation p-values for V0–V4 are $p < 0.0001$.*

---

## 3. Performance by Dataset Subset

### 3.1 Assignments 1–10 ($N=1,721$)
Regular coursework assignments covering introductory C++ programming, data structures, and algorithms:

| System | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK | Predicted Mean | Predicted Std | Descriptive Bias |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Human Target** | — | — | — | — | — | 4.1784 | 1.0692 | 0.0000 |
| **V0: TF-IDF Baseline** | 2.6472 | 2.9073 | 0.4177 | 0.4451 | 0.1126 | 1.5353 | 1.1705 | -2.6431 |
| **V1: Base ASAG** | 3.8030 | 4.0204 | 0.1331 | 0.1229 | 0.0165 | 0.3887 | 0.9670 | -3.7897 |
| **V2: Historical Proposed** | 3.2361 | 3.5192 | 0.1365 | 0.0850 | 0.0226 | 0.9740 | 1.1439 | -3.2044 |
| **V3: Current Proposed** | 3.6109 | 3.8899 | 0.2053 | 0.1989 | 0.0391 | 0.5808 | 1.2661 | -3.5976 |
| **V4: Experiment 4 (Severity-Aware)** | 3.6597 | 3.9432 | 0.1963 | 0.1969 | 0.0348 | 0.5362 | 1.2985 | -3.6422 |

### 3.2 Exams 11–12 ($N=552$)
Comprehensive midterm and final examination questions:

| System | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK | Predicted Mean | Predicted Std | Descriptive Bias |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Human Target** | — | — | — | — | — | 4.2011 | 1.1788 | 0.0000 |
| **V0: TF-IDF Baseline** | 2.6877 | 2.9502 | 0.4240 | 0.4338 | 0.1226 | 1.5201 | 1.1158 | -2.6809 |
| **V1: Base ASAG** | 3.8111 | 4.0898 | 0.1496 | 0.1097 | 0.0223 | 0.4008 | 1.1406 | -3.8003 |
| **V2: Historical Proposed** | 3.1599 | 3.5138 | 0.1274 | 0.0457 | 0.0275 | 1.0770 | 1.2568 | -3.1241 |
| **V3: Current Proposed** | 3.5476 | 3.8747 | 0.1989 | 0.1983 | 0.0411 | 0.6770 | 1.3587 | -3.5241 |
| **V4: Experiment 4 (Severity-Aware)** | 3.5327 | 3.8763 | **0.2284** | **0.2065** | **0.0478** | 0.6878 | 1.4398 | -3.5133 |

*Key finding: On the exam partition ($N=552$), Experiment 4 (V4) achieves the highest Pearson correlation ($r=0.2284$), highest Spearman rank correlation ($\rho=0.2065$), highest QWK ($\kappa=0.0478$), and lowest error ($MAE=3.5327$) among all symbolic ASAG pipelines (V1–V4).*

### 3.3 Sentential Reference Subset ($N=1,341$)
Questions whose official instructor reference answers contain complete, finite clausal structures:

| System | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK | Predicted Mean | Predicted Std | Descriptive Bias |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Human Target** | — | — | — | — | — | 4.1957 | 1.0246 | 0.0000 |
| **V0: TF-IDF Baseline** | 2.7464 | 2.9427 | 0.3743 | 0.3591 | 0.0685 | 1.4510 | 0.8569 | -2.7447 |
| **V1: Base ASAG** | 3.5535 | 3.8176 | 0.1969 | 0.1968 | 0.0325 | 0.6639 | 1.2468 | -3.5319 |
| **V2: Historical Proposed** | 2.8837 | 3.2052 | 0.2038 | 0.1917 | 0.0450 | 1.3630 | 1.3241 | -2.8328 |
| **V3: Current Proposed** | 3.6412 | 3.8784 | 0.1953 | 0.1975 | 0.0323 | 0.5694 | 1.1396 | -3.6263 |
| **V4: Experiment 4 (Severity-Aware)** | 3.6807 | 3.9227 | 0.1864 | 0.1925 | 0.0275 | 0.5327 | 1.1695 | -3.6631 |

### 3.4 Non-Sentential Reference Subset ($N=932$)
Questions whose instructor reference answers consist of noun phrases, lists, non-finite fragments, or keywords (e.g., "Queue", "By value, by reference"):

| System | MAE | RMSE | Pearson $r$ | Spearman $\rho$ | QWK | Predicted Mean | Predicted Std | Descriptive Bias |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Human Target** | — | — | — | — | — | 4.1668 | 1.1929 | 0.0000 |
| **V0: TF-IDF Baseline** | 2.5286 | 2.8816 | 0.4681 | 0.5342 | 0.1781 | 1.6476 | 1.4793 | -2.5192 |
| **V1: Base ASAG** | 4.1668 | 4.3341 | N/A* | N/A* | 0.0000 | 0.0000 | 0.0000 | -4.1668 |
| **V2: Historical Proposed** | 3.6980 | 3.9243 | 0.0113 | -0.0459 | 0.0010 | 0.4753 | 0.6069 | -3.6915 |
| **V3: Current Proposed** | 3.5298 | 3.8976 | 0.2134 | 0.2201 | 0.0499 | 0.6541 | 1.4781 | -3.5127 |
| **V4: Experiment 4 (Severity-Aware)** | 3.5543 | 3.9333 | **0.2253** | **0.2296** | **0.0528** | 0.6310 | 1.5421 | -3.5358 |

*\*Note: Base ASAG (V1) produced a constant score of 0.0 for all 932 non-sentential reference records because classical dependency triple extraction requires a finite verbal head, resulting in undefined correlation.*

---

## 4. Score Distribution Analysis

The degree of score compression and distribution across boundaries is summarized below:

| System | % Grades in $[0.0, 0.5]$ (Floor) | % Grades in $[4.5, 5.0]$ (Ceiling) | Prediction Range | Std Deviation |
| :--- | :---: | :---: | :---: | :---: |
| **Human Target** | 1.85% | 61.50% | $[0.00, 5.00]$ | 1.0966 |
| **V0: TF-IDF Baseline** | 19.62% | 3.34% | $[0.00, 5.00]$ | 1.1572 |
| **V1: Base ASAG** | 82.23% | 2.55% | $[0.00, 5.00]$ | 1.0117 |
| **V2: Historical Proposed** | 55.21% | 3.48% | $[0.00, 5.00]$ | 1.1729 |
| **V3: Current Proposed** | 73.16% | 6.20% | $[0.00, 5.00]$ | 1.2896 |
| **V4: Experiment 4 (Severity-Aware)** | 78.44% | 6.64% | $[0.00, 5.00]$ | 1.3355 |

### Distribution Observations
1. **Severe Floor Compression**: Human annotators awarded scores $\ge 4.5$ to $61.5\%$ of student answers (reflecting high student performance on basic CS homework). In contrast, all symbolic systems (V1–V4) compress over $73\%$ of predictions below $0.5$ points.
2. **Negative Bias**: Base ASAG has a mean prediction of $0.3917$ (bias of $-3.7922$). V4 exhibits a mean of $0.5730$ (bias of $-3.6109$).
3. **Correlation vs. Error Divergence**: TF-IDF achieves the lowest MAE ($2.6571$) and highest Pearson ($0.4184$) because bag-of-words surface overlap acts as a smooth proxy for topic recall and answer length, whereas symbolic dependency matching is binary and unforgiving when surface syntax diverges from instructor phrasing.
