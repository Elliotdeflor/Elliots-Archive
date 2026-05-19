import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


class ElliotFeatureSelection:
    """
    Permutation-null feature selection using RandomForest impurity importances.

    New additions:
      1) std_threshold defaults to None:
         - If std_threshold is None, we run an internal std sweep over {0,1,2,3}
           and pick the best threshold using a validation split.
         - If std_threshold is provided (not None), we DO NOT run the sweep.

      2) prune_ratio:
         - Caps how aggressive pruning can be.
         - Interpretation: maximum fraction of features you are allowed to DROP.
           Example: prune_ratio=0.7 means you may drop up to 70% of features,
           i.e. must keep at least 30%.
         - The selector will top-up selected features with highest real importance
           to meet the minimum-keep constraint if needed.
    """

    def __init__(
        self,
        n_iter: int = 50,
        std_threshold: float | None = None,   # <- default None
        random_state: int = 42,
        n_estimators: int = 200,
        prune_ratio: float = 0.8,             # <- new
        val_size: float = 0.25                # internal validation size for std sweep
    ):
        self.n_iter = int(n_iter)
        self.std_threshold = std_threshold
        self.random_state = int(random_state)
        self.n_estimators = int(n_estimators)
        self.prune_ratio = float(prune_ratio)
        self.val_size = float(val_size)

        self.selected_features: list[str] = []
        self.feature_distributions: dict[str, list[float]] = {}
        self.real_importances: dict[str, float] = {}
        self.best_std_threshold_: float | None = None
        self._fit_summary_: dict = {}

    # -----------------------------
    # Core helpers
    # -----------------------------
    def _compute_null_distributions(self, X: pd.DataFrame, y: np.ndarray):
        rng = np.random.default_rng(self.random_state)
        feature_importances = {col: [] for col in X.columns}

        # Null: shuffle each column independently (your original design)
        for i in range(self.n_iter):
            X_shuffled = X.copy()
            for col in X.columns:
                X_shuffled[col] = rng.permutation(X_shuffled[col].to_numpy())

            rf = RandomForestClassifier(
                n_estimators=self.n_estimators,
                random_state=int(rng.integers(0, 2**31 - 1)),
                n_jobs=-1
            )
            rf.fit(X_shuffled, y)

            for col, imp in zip(X.columns, rf.feature_importances_):
                feature_importances[col].append(float(imp))

        self.feature_distributions = feature_importances

        null_mean = {c: float(np.mean(v)) for c, v in feature_importances.items()}
        null_std = {c: float(np.std(v, ddof=1)) for c, v in feature_importances.items()}
        return null_mean, null_std

    def _compute_real_importances(self, X: pd.DataFrame, y: np.ndarray):
        rng = np.random.default_rng(self.random_state)
        rf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            random_state=int(rng.integers(0, 2**31 - 1)),
            n_jobs=-1
        )
        rf.fit(X, y)
        self.real_importances = dict(zip(X.columns, map(float, rf.feature_importances_)))
        return self.real_importances

    def _select_with_threshold(self, X: pd.DataFrame, null_mean: dict, null_std: dict, std_k: float):
        # Raw threshold selection
        selected = [
            c for c in X.columns
            if self.real_importances[c] > (null_mean[c] + std_k * null_std[c])
        ]

        # Always select at least 1
        if not selected:
            selected = [max(self.real_importances, key=self.real_importances.get)]

        # Enforce prune_ratio (minimum keep)
        d = X.shape[1]
        if not (0.0 <= self.prune_ratio < 1.0):
            raise ValueError("prune_ratio must be in [0.0, 1.0). Example: 0.8 means drop up to 80%.")

        min_keep = max(1, int(np.ceil(d * (1.0 - self.prune_ratio))))

        if len(selected) < min_keep:
            # Top-up with highest real-importance features
            ranked = sorted(self.real_importances.items(), key=lambda kv: kv[1], reverse=True)
            ranked_cols = [c for c, _ in ranked]
            for c in ranked_cols:
                if c not in selected:
                    selected.append(c)
                if len(selected) >= min_keep:
                    break

        return selected

    def _score_selected_set(self, X_train, y_train, X_val, y_val, selected_features):
        # Simple validation model for threshold sweep
        rf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1
        )
        rf.fit(X_train[selected_features], y_train)
        pred = rf.predict(X_val[selected_features])
        return float(accuracy_score(y_val, pred))

    # -----------------------------
    # Public API
    # -----------------------------
    def fit(self, X: pd.DataFrame, y):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X must be a pandas DataFrame with named columns.")
        y = np.asarray(y).ravel()

        # Compute null distributions + real importances once
        null_mean, null_std = self._compute_null_distributions(X, y)
        self._compute_real_importances(X, y)

        # If std_threshold is provided, DO NOT run the sweep.
        if self.std_threshold is not None:
            k = float(self.std_threshold)
            self.selected_features = self._select_with_threshold(X, null_mean, null_std, k)
            self.best_std_threshold_ = k
            self._fit_summary_ = {
                "mode": "fixed_std",
                "std_threshold": k,
                "selected_n": len(self.selected_features),
                "original_d": X.shape[1],
                "min_keep_from_prune_ratio": int(np.ceil(X.shape[1] * (1.0 - self.prune_ratio))),
            }
            return self

        # Otherwise: sweep std thresholds in {0,1,2,3} and pick best by validation accuracy.
        std_grid = [0.0, 1.0, 2.0, 3.0]

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=self.val_size, stratify=y, random_state=self.random_state
        )

        best_k = None
        best_score = -np.inf
        best_features = None
        scores_by_k = {}

        for k in std_grid:
            feats = self._select_with_threshold(X_train, null_mean, null_std, k)
            score = self._score_selected_set(X_train, y_train, X_val, y_val, feats)
            scores_by_k[k] = score

            if score > best_score:
                best_score = score
                best_k = k
                best_features = feats

        self.selected_features = list(best_features)
        self.best_std_threshold_ = float(best_k)
        self._fit_summary_ = {
            "mode": "std_sweep",
            "std_grid": std_grid,
            "scores_by_std": scores_by_k,
            "best_std": float(best_k),
            "best_val_acc": float(best_score),
            "selected_n": len(self.selected_features),
            "original_d": X.shape[1],
            "min_keep_from_prune_ratio": int(np.ceil(X.shape[1] * (1.0 - self.prune_ratio))),
        }
        return self

    def transform(self, X: pd.DataFrame):
        if not self.selected_features:
            raise RuntimeError("ElliotFeatureSelection has not been fit yet.")
        return X[self.selected_features]

    def fit_transform(self, X: pd.DataFrame, y):
        return self.fit(X, y).transform(X)
