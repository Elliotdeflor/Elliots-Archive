"""
ElliotFS paper tables + figures generator

Reads the benchmark CSV (elliot_feature_selection_results.csv) and:
  - Prints paper-ready tables (I–IV) to console
  - Saves tables as CSVs
  - Creates and saves figures (PNG) for:
      Fig. 2 retained features
      Fig. 3 mean test accuracy
      Fig. 4 mean improvement vs baseline (+ error bars)
      Fig. 5 std of improvement (stability)

Usage:
  python paper_outputs.py --results_csv "elliot_feature_selection_results.csv"

Optional:
  python paper_outputs.py --results_csv "elliot_feature_selection_results.csv" --out_dir "paper_outputs"

Notes:
  - If an improvement summary CSV is provided, it will be used.
  - Otherwise, the script computes improvement vs baseline from the results CSV.
"""

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------------------
# Helpers
# ---------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def print_table(title: str, df: pd.DataFrame, max_rows: int = 200) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    if len(df) > max_rows:
        print(df.head(max_rows).to_string(index=False))
        print(f"... ({len(df) - max_rows} more rows)")
    else:
        print(df.to_string(index=False))


def compute_improvement_summary(
    results: pd.DataFrame,
    accuracy_col: str = "test_acc",
    baseline_name: str = "Baseline",
    key_cols=("dataset", "run"),
) -> pd.DataFrame:
    """
    Paired improvement by (dataset, run):
      improvement = acc(method) - acc(baseline)
    Aggregates mean/std across runs for each dataset/method.
    """
    required = {"dataset", "method", accuracy_col, "run"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Results CSV missing required columns: {missing}")

    base = (
        results[results["method"] == baseline_name]
        .loc[:, list(key_cols) + [accuracy_col]]
        .rename(columns={accuracy_col: "baseline_acc"})
    )
    if base.empty:
        raise ValueError(f"No baseline rows found for method='{baseline_name}'")

    merged = results.merge(base, on=list(key_cols), how="inner")
    merged["improvement"] = merged[accuracy_col] - merged["baseline_acc"]
    merged = merged[merged["method"] != baseline_name].copy()

    out = (
        merged.groupby(["dataset", "method"])["improvement"]
        .agg(
            mean_improvement="mean",
            std_improvement=lambda x: x.std(ddof=1),
            n_runs="count",
        )
        .reset_index()
        .sort_values(["dataset", "mean_improvement"], ascending=[True, False])
    )
    return out


def format_mean_std(mean_val: float, std_val: float, decimals: int = 3) -> str:
    if pd.isna(std_val):
        return f"{mean_val:.{decimals}f}"
    return f"{mean_val:.{decimals}f} ± {std_val:.{decimals}f}"


def save_plot(figpath: str) -> None:
    plt.tight_layout()
    plt.savefig(figpath, dpi=250, bbox_inches="tight")
    plt.close()


# ---------------------------
# Tables
# ---------------------------

def make_table_I_dataset_summary(results: pd.DataFrame) -> pd.DataFrame:
    """
    Table I: Dataset summary
    NOTE: 'Evaluations' = number of rows in results for that dataset.
          This equals (methods * runs) and is not 'samples' in dataset.
          True sample count isn't stored in the CSV unless you logged it.
    """
    table = (
        results.groupby("dataset")
        .agg(
            evaluations=("run", "count"),
            features=("d_original", "first"),
            classes=("n_classes", "first"),
        )
        .reset_index()
        .rename(
            columns={
                "dataset": "Dataset",
                "features": "Features",
                "classes": "Classes",
                "evaluations": "Evaluations",
            }
        )
        .sort_values("Dataset")
    )
    return table


def make_table_II_retained_dimensionality(results: pd.DataFrame) -> pd.DataFrame:
    """
    Table II: mean retained features ± std
    """
    table = (
        results.groupby(["dataset", "method"])["d_retained"]
        .agg(mean_retained="mean", std_retained=lambda x: x.std(ddof=1), n="count")
        .reset_index()
        .rename(columns={"dataset": "Dataset", "method": "Method"})
        .sort_values(["Dataset", "Method"])
    )
    return table


def make_table_III_test_accuracy(results: pd.DataFrame) -> pd.DataFrame:
    """
    Table III: test accuracy mean ± std
    """
    table = (
        results.groupby(["dataset", "method"])["test_acc"]
        .agg(mean_test_acc="mean", std_test_acc=lambda x: x.std(ddof=1), n="count")
        .reset_index()
        .rename(columns={"dataset": "Dataset", "method": "Method"})
        .sort_values(["Dataset", "Method"])
    )
    return table


def make_table_IV_improvement(improvement: pd.DataFrame) -> pd.DataFrame:
    """
    Table IV: improvement vs baseline (paired)
    """
    table = improvement.rename(
        columns={
            "dataset": "Dataset",
            "method": "Method",
            "mean_improvement": "Mean_Delta_Acc",
            "std_improvement": "Std_Delta_Acc",
            "n_runs": "Runs",
        }
    ).sort_values(["Dataset", "Mean_Delta_Acc"], ascending=[True, False])
    return table


# ---------------------------
# Figures
# ---------------------------

def fig2_retained_features(table_II: pd.DataFrame, out_dir: str) -> None:
    """
    Fig. 2: Mean retained features by method for each dataset
    Output: one figure per dataset (readable) + one combined (optional)
    """
    for dataset in table_II["Dataset"].unique():
        d = table_II[table_II["Dataset"] == dataset].copy()
        d = d.sort_values("mean_retained", ascending=False)

        plt.figure()
        plt.bar(d["Method"], d["mean_retained"], yerr=d["std_retained"], capsize=6)
        plt.title(f"Fig. 2 — Mean Retained Features (±1 std)\n{dataset}")
        plt.ylabel("Retained Features")
        plt.xticks(rotation=20, ha="right")
        save_plot(os.path.join(out_dir, f"fig2_retained_features__{safe_name(dataset)}.png"))


def fig3_mean_test_accuracy(table_III: pd.DataFrame, out_dir: str) -> None:
    """
    Fig. 3: Mean test accuracy by method for each dataset
    """
    for dataset in table_III["Dataset"].unique():
        d = table_III[table_III["Dataset"] == dataset].copy()
        d = d.sort_values("mean_test_acc", ascending=False)

        plt.figure()
        plt.bar(d["Method"], d["mean_test_acc"], yerr=d["std_test_acc"], capsize=6)
        plt.title(f"Fig. 3 — Mean Test Accuracy (±1 std)\n{dataset}")
        plt.ylabel("Test Accuracy")
        plt.ylim(0, 1.0)
        plt.xticks(rotation=20, ha="right")
        save_plot(os.path.join(out_dir, f"fig3_mean_test_accuracy__{safe_name(dataset)}.png"))


def fig4_improvement_vs_baseline(table_IV: pd.DataFrame, out_dir: str) -> None:
    """
    Fig. 4: Mean Δ accuracy vs baseline with error bars
    """
    for dataset in table_IV["Dataset"].unique():
        d = table_IV[table_IV["Dataset"] == dataset].copy()
        d = d.sort_values("Mean_Delta_Acc", ascending=False)

        plt.figure()
        plt.bar(d["Method"], d["Mean_Delta_Acc"], yerr=d["Std_Delta_Acc"], capsize=6)
        plt.axhline(0)
        plt.title(f"Fig. 4 — Mean Δ Test Accuracy vs Baseline (±1 std)\n{dataset}")
        plt.ylabel("Δ Test Accuracy")
        plt.xticks(rotation=20, ha="right")
        save_plot(os.path.join(out_dir, f"fig4_improvement_vs_baseline__{safe_name(dataset)}.png"))


def fig5_stability_std_improvement(table_IV: pd.DataFrame, out_dir: str) -> None:
    """
    Fig. 5: Std of Δ accuracy vs baseline (stability comparison)
    Lower is better (more stable).
    """
    for dataset in table_IV["Dataset"].unique():
        d = table_IV[table_IV["Dataset"] == dataset].copy()
        d = d.sort_values("Std_Delta_Acc", ascending=True)

        plt.figure()
        plt.bar(d["Method"], d["Std_Delta_Acc"])
        plt.title(f"Fig. 5 — Stability (Std of Δ Accuracy)\n{dataset}")
        plt.ylabel("Std(Δ Test Accuracy)")
        plt.xticks(rotation=20, ha="right")
        save_plot(os.path.join(out_dir, f"fig5_stability_std_delta__{safe_name(dataset)}.png"))


def safe_name(s: str) -> str:
    keep = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_"):
            keep.append(ch)
        elif ch.isspace():
            keep.append("_")
    return "".join(keep)[:120]


# ---------------------------
# Main
# ---------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results_csv", type=str, default="elliot_feature_selection_results.csv")
    ap.add_argument("--improvement_csv", type=str, default=None,
                    help="Optional: improvement summary CSV. If omitted, it will be computed from results_csv.")
    ap.add_argument("--out_dir", type=str, default="paper_outputs")
    ap.add_argument("--baseline_name", type=str, default="Baseline")
    args = ap.parse_args()

    if not os.path.exists(args.results_csv):
        raise FileNotFoundError(f"results_csv not found: {args.results_csv}")

    ensure_dir(args.out_dir)

    print(f">>> Loading results: {args.results_csv}")
    results = pd.read_csv(args.results_csv)

    # Improvement summary: load or compute
    if args.improvement_csv and os.path.exists(args.improvement_csv):
        print(f">>> Loading improvement summary: {args.improvement_csv}")
        improvement = pd.read_csv(args.improvement_csv)
    else:
        print(">>> Computing improvement summary vs baseline from results CSV")
        improvement = compute_improvement_summary(
            results,
            accuracy_col="test_acc",
            baseline_name=args.baseline_name
        )

    # Build tables
    table_I = make_table_I_dataset_summary(results)
    table_II = make_table_II_retained_dimensionality(results)
    table_III = make_table_III_test_accuracy(results)
    table_IV = make_table_IV_improvement(improvement)

    # Print tables (paper-ready)
    print_table("Table I — Dataset Summary", table_I)
    print_table("Table II — Retained Dimensionality (mean ± std)", table_II)
    print_table("Table III — Test Accuracy (mean ± std)", table_III)
    print_table("Table IV — Paired Improvement vs Baseline (mean ± std)", table_IV)

    # Save tables as CSV
    t1_path = os.path.join(args.out_dir, "table_I_dataset_summary.csv")
    t2_path = os.path.join(args.out_dir, "table_II_retained_dimensionality.csv")
    t3_path = os.path.join(args.out_dir, "table_III_test_accuracy.csv")
    t4_path = os.path.join(args.out_dir, "table_IV_improvement_vs_baseline.csv")

    table_I.to_csv(t1_path, index=False)
    table_II.to_csv(t2_path, index=False)
    table_III.to_csv(t3_path, index=False)
    table_IV.to_csv(t4_path, index=False)

    print("\n>>> Saved tables:")
    print(f"    - {t1_path}")
    print(f"    - {t2_path}")
    print(f"    - {t3_path}")
    print(f"    - {t4_path}")

    # Create figures
    print("\n>>> Creating figures...")
    fig2_retained_features(table_II, args.out_dir)
    fig3_mean_test_accuracy(table_III, args.out_dir)
    fig4_improvement_vs_baseline(table_IV, args.out_dir)
    fig5_stability_std_improvement(table_IV, args.out_dir)

    print("\n>>> Figures saved to:")
    print(f"    - {args.out_dir}")
    print("\nDone.")


if __name__ == "__main__":
    main()
