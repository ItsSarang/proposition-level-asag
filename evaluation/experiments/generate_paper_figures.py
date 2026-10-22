"""
Generate Publication-Quality IEEE Research Paper Figures for Proposition-Level ASAG.

Outputs:
1. reports/figures/fig1_overall_performance.png
   - Grouped bar chart comparing MAE, RMSE, Pearson r, Spearman rho, and QWK across Model 1, Model 2, Model 3.
2. reports/figures/fig2_score_distributions.png
   - Kernel Density Estimation (KDE) plot comparing grade distributions: Human Gold vs. Model 1 vs. Model 2 vs. Model 3.
3. reports/figures/fig3_sentential_fragility.png
   - Clustered bar chart comparing Pearson r and MAE across Sentential (N=1,341) and Non-Sentential (N=932) questions.
4. reports/figures/fig4_ablation_progression.png
   - Multi-stage ablation step chart showing Pearson r climbing and MAE falling across the 4 architecture stages.
5. reports/figures/fig5_scatter_correlation.png
   - 3-panel scatter plot with regression trendlines for Model 1, Model 2, and Model 3 against Human Gold.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Set publication style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.size": 11,
    "font.family": "sans-serif",
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
})

COLORS = {
    "human": "#2b2d42",        # Slate dark
    "model1": "#457b9d",       # Steel blue
    "model2": "#e63946",       # Crimson coral
    "model3": "#2a9d8f",       # Teal emerald
    "model3_sym": "#f4a261",   # Sandy orange
}

OUT_DIR = Path("reports/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = Path("evaluation/results/three_models_comparison/three_models_predictions.csv")
if not CSV_PATH.exists():
    raise FileNotFoundError(f"Predictions file not found: {CSV_PATH}")

df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} records from {CSV_PATH}")

# -------------------------------------------------------------
# Figure 1: Overall Performance Comparison (Grouped Bar Chart)
# -------------------------------------------------------------
def plot_fig1_overall_performance():
    metrics = ["MAE (↓)", "RMSE (↓)", "Pearson r (↑)", "Spearman ρ (↑)", "QWK (↑)"]
    m1_vals = [2.6571, 2.9178, 0.4184, 0.4424, 0.1151]
    m2_vals = [3.8041, 4.0365, 0.1383, 0.1179, 0.0180]
    m3_vals = [1.1929, 1.8242, 0.4574, 0.4715, 0.3557]

    x = np.arange(len(metrics))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9, 5))
    rects1 = ax.bar(x - width, m1_vals, width, label="Model 1: TF-IDF Baseline", color=COLORS["model1"], edgecolor="black", alpha=0.9)
    rects2 = ax.bar(x, m2_vals, width, label="Model 2: Base ASAG (Clausal Triples)", color=COLORS["model2"], edgecolor="black", alpha=0.9)
    rects3 = ax.bar(x + width, m3_vals, width, label="Model 3: Proposed ASAG (Calibrated)", color=COLORS["model3"], edgecolor="black", alpha=0.95)

    ax.set_ylabel("Metric Score", fontweight="bold")
    ax.set_title("Overall Benchmark Performance Comparison (N = 2,273)", fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc", loc="upper right")
    ax.set_ylim(0, 4.6)

    # Add data labels
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f"{height:.2f}",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8.5, fontweight="semibold")

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    plt.tight_layout()
    out_path = OUT_DIR / "fig1_overall_performance.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")

# -------------------------------------------------------------
# Figure 2: Prediction Density Distribution vs. Human Ground Truth
# -------------------------------------------------------------
def plot_fig2_score_distributions():
    fig, ax = plt.subplots(figsize=(9, 5))

    sns.kdeplot(df["human_score"], ax=ax, label="Human Gold Standard (Mean=4.18)", color=COLORS["human"], linewidth=2.5, linestyle="--")
    sns.kdeplot(df["v0_grade"], ax=ax, label="Model 1: TF-IDF Baseline (Mean=1.53)", color=COLORS["model1"], linewidth=2.0)
    sns.kdeplot(df["v1_grade"], ax=ax, label="Model 2: Base ASAG (81.4% Zeros, Mean=0.39)", color=COLORS["model2"], linewidth=2.0)
    sns.kdeplot(df["v5_calibrated_grade"], ax=ax, label="Model 3: Proposed ASAG (Calibrated, Mean=3.48)", color=COLORS["model3"], linewidth=2.5)

    ax.set_xlim(-0.2, 5.2)
    ax.set_xlabel("Assigned Grade (0.0 to 5.0 Scale)", fontweight="bold")
    ax.set_ylabel("Probability Density", fontweight="bold")
    ax.set_title("Grade Distribution Density: System Predictions vs. Human Gold Standard", fontweight="bold", pad=12)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc", loc="upper center")

    # Annotate the zero-spike
    ax.annotate("Model 2 Zero-Inflation Spike\n(81.4% exact zeros)",
                xy=(0.0, 1.25), xytext=(0.8, 1.35),
                arrowprops=dict(facecolor=COLORS["model2"], shrink=0.08, width=1.5, headwidth=6),
                fontweight="bold", color=COLORS["model2"], fontsize=9.5)

    # Annotate human leniency peak
    ax.annotate("Human Leniency Peak\n(Charitable 5.0/5.0 grading)",
                xy=(4.8, 0.65), xytext=(3.0, 0.85),
                arrowprops=dict(facecolor=COLORS["human"], shrink=0.08, width=1.5, headwidth=6),
                fontweight="bold", color=COLORS["human"], fontsize=9.5)

    plt.tight_layout()
    out_path = OUT_DIR / "fig2_score_distributions.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")

# -------------------------------------------------------------
# Figure 3: Sentential vs. Non-Sentential Robustness Comparison
# -------------------------------------------------------------
def plot_fig3_sentential_fragility():
    subsets = ["Sentential Questions (N=1,341)", "Non-Sentential Questions (N=932)"]

    # Correlation comparison
    m1_r = [0.3743, 0.4681]
    m2_r = [0.1975, 0.0000]
    m3_r = [0.3835, 0.5359]

    # MAE comparison
    m1_mae = [2.7464, 2.5286]
    m2_mae = [3.5520, 4.1668]
    m3_mae = [1.0894, 1.3417]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8))
    x = np.arange(len(subsets))
    width = 0.24

    # Subplot 1: Pearson r
    ax1.bar(x - width, m1_r, width, label="Model 1 (TF-IDF)", color=COLORS["model1"], edgecolor="black")
    ax1.bar(x, m2_r, width, label="Model 2 (Base ASAG)", color=COLORS["model2"], edgecolor="black")
    ax1.bar(x + width, m3_r, width, label="Model 3 (Proposed)", color=COLORS["model3"], edgecolor="black")
    ax1.set_ylabel("Pearson Correlation r (↑)", fontweight="bold")
    ax1.set_title("Rank Alignment Across Reference Syntax", fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(subsets, fontweight="bold", fontsize=9.5)
    ax1.set_ylim(0, 0.65)
    ax1.legend(loc="upper left")

    # Annotate collapse
    ax1.annotate("Model 2 Collapse\n(r = 0.0000)", xy=(1.0, 0.02), xytext=(0.75, 0.18),
                 arrowprops=dict(facecolor=COLORS["model2"], shrink=0.08, width=1.2, headwidth=5),
                 fontweight="bold", color=COLORS["model2"], fontsize=9)

    # Subplot 2: MAE
    ax2.bar(x - width, m1_mae, width, label="Model 1 (TF-IDF)", color=COLORS["model1"], edgecolor="black")
    ax2.bar(x, m2_mae, width, label="Model 2 (Base ASAG)", color=COLORS["model2"], edgecolor="black")
    ax2.bar(x + width, m3_mae, width, label="Model 3 (Proposed)", color=COLORS["model3"], edgecolor="black")
    ax2.set_ylabel("Mean Absolute Error MAE (↓)", fontweight="bold")
    ax2.set_title("Scoring Error Across Reference Syntax", fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(subsets, fontweight="bold", fontsize=9.5)
    ax2.set_ylim(0, 4.8)
    ax2.legend(loc="upper left")

    plt.suptitle("Syntactic Fragility Analysis: Sentential vs. Non-Sentential Reference Rubrics", fontweight="bold", y=1.02)
    plt.tight_layout()
    out_path = OUT_DIR / "fig3_sentential_fragility.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path}")

# -------------------------------------------------------------
# Figure 4: Component Contribution Ablation Progression
# -------------------------------------------------------------
def plot_fig4_ablation_progression():
    stages = [
        "Stage 1:\nBase ASAG\n(Model 2)",
        "Stage 2:\n+ Canonical\nFragments",
        "Stage 3:\n+ Proposition\nSeverity D2",
        "Stage 4:\nModel 3 Full\n(+ Calibration)"
    ]
    r_overall = [0.1383, 0.2487, 0.2616, 0.4574]
    r_nonsent = [0.0000, 0.2951, 0.2985, 0.5359]
    mae_overall = [3.8041, 3.4391, 3.3358, 1.1929]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    x = np.arange(len(stages))

    # Line 1: Overall Pearson r (left axis)
    color1 = COLORS["model3"]
    line1 = ax1.plot(x, r_overall, marker="o", linewidth=2.5, color=color1, markersize=8, label="Overall Pearson r (↑)")
    line2 = ax1.plot(x, r_nonsent, marker="s", linewidth=2.2, color="#e76f51", linestyle="--", markersize=7, label="Non-Sentential Pearson r (↑)")
    ax1.set_ylabel("Pearson Correlation (r)", fontweight="bold", color=color1)
    ax1.set_ylim(-0.05, 0.60)
    ax1.tick_params(axis="y", labelcolor=color1)

    # Line 2: MAE (right axis)
    ax2 = ax1.twinx()
    color2 = COLORS["model2"]
    line3 = ax2.plot(x, mae_overall, marker="^", linewidth=2.5, color=color2, markersize=8, label="Overall MAE (↓)")
    ax2.set_ylabel("Mean Absolute Error (MAE)", fontweight="bold", color=color2)
    ax2.set_ylim(0.8, 4.2)
    ax2.tick_params(axis="y", labelcolor=color2)

    ax1.set_xticks(x)
    ax1.set_xticklabels(stages, fontweight="bold")
    ax1.set_title("Ablation Progression: Component Impact on Correlation and Error", fontweight="bold", pad=12)

    # Combine legends
    lines = line1 + line2 + line3
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="center left", frameon=True, facecolor="white", edgecolor="#cccccc")

    plt.tight_layout()
    out_path = OUT_DIR / "fig4_ablation_progression.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Generated {out_path}")

# -------------------------------------------------------------
# Figure 5: 3-Panel Scatter Plot with Regression Lines
# -------------------------------------------------------------
def plot_fig5_scatter_correlation():
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)

    models = [
        ("v0_grade", "Model 1: TF-IDF Baseline", COLORS["model1"], 0.4184),
        ("v1_grade", "Model 2: Base ASAG", COLORS["model2"], 0.1383),
        ("v5_calibrated_grade", "Model 3: Proposed ASAG", COLORS["model3"], 0.4574),
    ]

    for ax, (col, title, color, r_val) in zip(axes, models):
        # Sample points with slight jitter for density visualization
        jitter_x = df[col] + np.random.normal(0, 0.05, len(df))
        jitter_y = df["human_score"] + np.random.normal(0, 0.05, len(df))

        ax.scatter(jitter_x, jitter_y, alpha=0.18, color=color, s=12, edgecolors="none")
        # Ideal line
        ax.plot([0, 5], [0, 5], color="#888888", linestyle=":", linewidth=1.5, label="Ideal (y = x)")

        # Linear regression trendline
        m, b = np.polyfit(df[col], df["human_score"], 1)
        ax.plot(np.array([0, 5]), m * np.array([0, 5]) + b, color="black", linewidth=2.0, label=f"Fit (r = {r_val:.4f})")

        ax.set_xlim(-0.2, 5.2)
        ax.set_ylim(-0.2, 5.2)
        ax.set_xlabel("Predicted Grade", fontweight="bold")
        ax.set_title(f"{title}", fontweight="bold", fontsize=11.5)
        ax.legend(loc="upper left", fontsize=9)

    axes[0].set_ylabel("Human Gold Grade", fontweight="bold")
    plt.suptitle("System Predictions vs. Human Gold Standard (N = 2,273 Active Answers)", fontweight="bold", y=1.02)
    plt.tight_layout()
    out_path = OUT_DIR / "fig5_scatter_correlation.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Generated {out_path}")

if __name__ == "__main__":
    plot_fig1_overall_performance()
    plot_fig2_score_distributions()
    plot_fig3_sentential_fragility()
    plot_fig4_ablation_progression()
    plot_fig5_scatter_correlation()
    print("All figures successfully generated in reports/figures/")
