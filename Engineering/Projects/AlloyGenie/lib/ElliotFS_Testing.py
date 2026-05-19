import os
import numpy as np
import pandas as pd

from sklearn.datasets import load_breast_cancer, load_digits, fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, confusion_matrix

from sklearn.feature_selection import (
    SelectKBest,
    mutual_info_classif,
    RFE,
    SelectFromModel
)

from sklearn.ensemble import RandomForestClassifier

# IMPORTANT:
# - This should import your UPDATED ElliotFeatureSelection class (with std sweep + prune_ratio).
from elliot_feature_selection import ElliotFeatureSelection


# ============================================================
# Configuration
# ============================================================

N_RUNS = 50
TEST_SIZE = 0.25
RANDOM_SEEDS = np.random.randint(0, 10_000, size=N_RUNS)

K_MODERATE = 32
K_HEAVY = 50

# NEW: If STD_THRESHOLD is None => EFS runs std sweep {0,1,2,3}
# If you set STD_THRESHOLD to a number (e.g., 1.0) => sweep is OFF
STD_THRESHOLD = None  # <- as you requested: input as None initially

# NEW: Cap maximum pruning aggressiveness.
# prune_ratio = max fraction of features allowed to DROP.
# e.g. 0.8 => can drop up to 80%, must keep at least 20%
PRUNE_RATIO = 0.8

# NEW: internal validation split size used by EFS when std sweep is enabled
EFS_VAL_SIZE = 0.25

CSV_PATH = "elliot_feature_selection_results.csv"

print(">>> Initialising experiment")
print(f">>> CSV output: {CSV_PATH}")
print(f">>> N_RUNS={N_RUNS} | TEST_SIZE={TEST_SIZE}")
print(f">>> ElliotFS: STD_THRESHOLD={STD_THRESHOLD} | PRUNE_RATIO={PRUNE_RATIO} | EFS_VAL_SIZE={EFS_VAL_SIZE}")

# Create CSV with header if it does not exist
if not os.path.exists(CSV_PATH):
    pd.DataFrame(columns=[
        "dataset", "method", "run", "seed",
        "train_acc", "test_acc",
        "TP", "FP", "TN", "FN",
        "n_classes",
        "d_original", "d_retained",

        # NEW: log EFS hyperparams + sweep result (filled for ElliotFS rows, NA for others)
        "efs_std_input",
        "efs_prune_ratio",
        "efs_val_size",
        "efs_best_std"
    ]).to_csv(CSV_PATH, index=False)


# ============================================================
# Dataset loaders
# ============================================================

def load_dataset_breast_cancer():
    ds = load_breast_cancer()
    return (
        "Breast Cancer (low redundancy)",
        pd.DataFrame(ds.data, columns=ds.feature_names),
        ds.target
    )


def load_dataset_digits():
    ds = load_digits()
    return (
        "Digits (moderate redundancy)",
        pd.DataFrame(ds.data, columns=[f"px_{i}" for i in range(ds.data.shape[1])]),
        ds.target
    )


def load_openml_dataset_by_name(candidates, description):
    last_err = None
    for name, version in candidates:
        try:
            print(f">>> OpenML fetch: {name} ({version})")
            ds = fetch_openml(name=name, version=version, as_frame=True)
            return description, ds.data, LabelEncoder().fit_transform(ds.target)
        except Exception as e:
            last_err = e
            print(f">>> Failed: {name} → {type(e).__name__}")
    raise RuntimeError(description) from last_err


def load_dataset_har_or_fallback():
    try:
        return load_openml_dataset_by_name(
            [("HAR", "active"), ("HumanActivityRecognition", "active")],
            "HAR (moderate–high redundancy)"
        )
    except RuntimeError:
        return load_openml_dataset_by_name(
            [("phoneme", "active"), ("qsar-biodeg", "active")],
            "Fallback redundancy dataset"
        )


def load_dataset_madelon():
    ds = fetch_openml(name="madelon", version="active", as_frame=True)
    return (
        "Madelon (heavy redundancy)",
        ds.data,
        LabelEncoder().fit_transform(ds.target)
    )


DATASET_LOADERS = [
    load_dataset_breast_cancer,
    load_dataset_digits,
    load_dataset_madelon
]


# ============================================================
# Utilities
# ============================================================

def confusion_stats(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        tp = np.trace(cm)
        fp = cm.sum(axis=0).sum() - tp
        fn = cm.sum(axis=1).sum() - tp
        tn = cm.sum() - tp - fp - fn
    return int(tp), int(fp), int(tn), int(fn)


def run_experiment(X, y, selector, seed):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=seed
    )

    steps = []
    if selector is not None:
        steps.append(("selector", selector))

    steps.append((
        "clf",
        RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=1,
            random_state=seed,
            n_jobs=-1
        )
    ))

    pipe = Pipeline(steps)
    pipe.fit(X_train, y_train)

    y_train_pred = pipe.predict(X_train)
    y_test_pred = pipe.predict(X_test)

    tp, fp, tn, fn = confusion_stats(y_test, y_test_pred)

    return (
        float(accuracy_score(y_train, y_train_pred)),
        float(accuracy_score(y_test, y_test_pred)),
        tp, fp, tn, fn
    )


# ============================================================
# Main benchmark
# ============================================================

for loader in DATASET_LOADERS:

    try:
        dataset_name, X, y = loader()
    except Exception as e:
        print(f">>> Dataset skipped: {e}")
        continue

    d_original = X.shape[1]
    print(f"\n>>> Dataset: {dataset_name}")
    print(f">>> Samples={X.shape[0]} | Features={d_original}")

    k = min(K_MODERATE, d_original) if d_original <= 100 else min(K_HEAVY, d_original)
    print(f">>> Comparator K (MI/RFE) = {k}")

    selectors = {
        "Baseline": None,
        "MutualInfo": SelectKBest(mutual_info_classif, k=k),
        "RFE": RFE(
            estimator=RandomForestClassifier(n_estimators=150, random_state=0, n_jobs=-1),
            n_features_to_select=k
        ),
        # NOTE: RandomForest is NOT a great L1 "embedded" model; kept for compatibility with your existing script.
        # If you want a true L1 embedded comparator, use LogisticRegression(penalty="l1") and add a scaler.
        "L1": SelectFromModel(
            RandomForestClassifier(n_estimators=200, random_state=0, n_jobs=-1)
        )
    }

    for run_idx, seed in enumerate(RANDOM_SEEDS, start=1):
        print(f">>> Run {run_idx}/{N_RUNS} | seed={seed}")

        # ------------------------------------------------------------
        # ElliotFS pruning (NEW: supports std sweep if STD_THRESHOLD=None)
        # ------------------------------------------------------------
        print("    - ElliotFS: fit_transform (with std sweep if enabled)")
        efs = ElliotFeatureSelection(
            std_threshold=STD_THRESHOLD,      # None => sweep 0..3, number => fixed
            prune_ratio=PRUNE_RATIO,
            random_state=seed,                # tie sweep randomness to this run
            val_size=EFS_VAL_SIZE
        )
        X_efs = efs.fit_transform(X, y)
        d_efs = X_efs.shape[1]
        best_std = getattr(efs, "best_std_threshold_", None)

        print(f"      ✓ ElliotFS complete | retained_d={d_efs}/{d_original} | best_std={best_std}")

        # ------------------------------------------------------------
        # Baselines and comparator selectors
        # ------------------------------------------------------------
        for method, selector in selectors.items():
            print(f"    - {method}: training/eval")

            if method == "Baseline":
                X_use = X
                sel = None
                d_retained = d_original
            else:
                X_use = X
                sel = selector
                d_retained = k

            train_acc, test_acc, tp, fp, tn, fn = run_experiment(X_use, y, sel, seed)

            pd.DataFrame([{
                "dataset": dataset_name,
                "method": method,
                "run": run_idx,
                "seed": seed,
                "train_acc": train_acc,
                "test_acc": test_acc,
                "TP": tp,
                "FP": fp,
                "TN": tn,
                "FN": fn,
                "n_classes": int(len(np.unique(y))),
                "d_original": int(d_original),
                "d_retained": int(d_retained),

                # EFS-only fields
                "efs_std_input": np.nan,
                "efs_prune_ratio": np.nan,
                "efs_val_size": np.nan,
                "efs_best_std": np.nan
            }]).to_csv(CSV_PATH, mode="a", header=False, index=False)

            print(f"      ✓ {method} logged")

        # ------------------------------------------------------------
        # ElliotFS evaluation row
        # ------------------------------------------------------------
        print("    - ElliotFS: training/eval (selected features)")
        train_acc, test_acc, tp, fp, tn, fn = run_experiment(X_efs, y, None, seed)

        pd.DataFrame([{
            "dataset": dataset_name,
            "method": "ElliotFS",
            "run": run_idx,
            "seed": seed,
            "train_acc": train_acc,
            "test_acc": test_acc,
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
            "n_classes": int(len(np.unique(y))),
            "d_original": int(d_original),
            "d_retained": int(d_efs),

            # EFS sweep metadata
            "efs_std_input": STD_THRESHOLD if STD_THRESHOLD is not None else "None",
            "efs_prune_ratio": PRUNE_RATIO,
            "efs_val_size": EFS_VAL_SIZE,
            "efs_best_std": best_std
        }]).to_csv(CSV_PATH, mode="a", header=False, index=False)

        print("      ✓ ElliotFS logged")

print("\n>>> Benchmark complete")
print(f">>> Results saved to: {CSV_PATH}")
