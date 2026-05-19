import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Paths
# ============================================================

INPUT_CSV = "elliot_feature_selection_results.csv"
OUTPUT_CSV = "elliot_feature_selection_improvement_summary.csv"

if not os.path.exists(INPUT_CSV):
    raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

print(f">>> Loading results from: {INPUT_CSV}")

df = pd.read_csv(INPUT_CSV)


# ============================================================
# Compute mean improvement vs baseline
# ============================================================

def compute_mean_improvement_vs_baseline(
    df: pd.DataFrame,
    accuracy_col: str = "test_acc",
    baseline_name: str = "Baseline"
):
    """
    Returns:
      dataset | method | mean_improvement | std_improvement | n_runs
    """

    base = (
        df[df["method"] == baseline_name]
        .loc[:, ["dataset", "run", accuracy_col]]
        .rename(columns={accuracy_col: "baseline_acc"})
    )

    if base.empty:
        raise ValueError("Baseline rows not found in CSV.")

    merged = df.merge(base, on=["dataset", "run"], how="inner")

    merged["improvement"] = merged[accuracy_col] - merged["baseline_acc"]

    merged = merged[merged["method"] != baseline_name]

    summary = (
        merged.groupby(["dataset", "method"])["improvement"]
        .agg(
            mean_improvement="mean",
            std_improvement=lambda x: x.std(ddof=1),
            n_runs="count"
        )
        .reset_index()
        .sort_values(["dataset", "mean_improvement"], ascending=[True, False])
    )

    return summary


summary_df = compute_mean_improvement_vs_baseline(df)

print("\n=== Mean accuracy improvement vs baseline ===")
print(summary_df.to_string(index=False))


# ============================================================
# Save summary table
# ============================================================

summary_df.to_csv(OUTPUT_CSV, index=False)
print(f"\n>>> Improvement summary saved to:\n{OUTPUT_CSV}")


# ============================================================
# Plot bar charts with error bars
# ============================================================

def plot_improvement_bars(summary_df, use_ci95=False):
    """
    One bar plot per dataset.
    Error bars = std (default) or 95% CI.
    """

    for dataset in summary_df["dataset"].unique():

        d = summary_df[summary_df["dataset"] == dataset].copy()

        if use_ci95:
            d["err"] = 1.96 * d["std_improvement"] / np.sqrt(d["n_runs"])
            err_label = "95% CI"
        else:
            d["err"] = d["std_improvement"]
            err_label = "Std dev"

        plt.figure()
        plt.bar(
            d["method"],
            d["mean_improvement"],
            yerr=d["err"],
            capsize=6
        )
        plt.axhline(0)
        plt.title(f"Mean Δ Test Accuracy vs Baseline\n{dataset}")
        plt.ylabel("Δ Test Accuracy")
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.show()


plot_improvement_bars(summary_df, use_ci95=False)
