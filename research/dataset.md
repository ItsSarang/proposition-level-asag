# Benchmark Dataset: Mohler CS ASAG Dataset v2.0

## Dataset Origin
- **Source**: University of North Texas (UNT) Computer Science Short Answer Dataset (Mohler et al., 2011).
- **Domain**: Undergraduate introductory Data Structures (CS2 / C++).
- **Size**:
  - Total Questions: 87
  - Active Questions: 81 (6 questions omitted matching published literature standards due to selection/code-ordering formats).
  - Total Student Answers: 2,442
  - Active Evaluated Records: 2,273
  - Inactive / Ignored Records: 169
- **Scale**: Human grades assigned from 0.0 to 5.0 points by two independent annotators.

## Inter-Annotator Agreement (Human Baseline)
On Assignments 1–10:
- **Pearson r**: 0.5910
- **Spearman rho**: 0.5855
- **MAE**: 0.7263
- **RMSE**: 1.2618

## Data Directory Structure
- `data/raw/mohler_asag/`: Original unmodified raw text and XML files.
- `data/processed/`: Standardized CSV files (`mohler_active_records.csv`, `mohler_all_records.csv`, etc.).
- `data/demo/`: Small demonstration examples for unit testing and interactive UI verification.
