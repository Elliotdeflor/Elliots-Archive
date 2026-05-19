from model_class import *

def add_noise_to_ml_df(model, noise_level=0.01, seed=42):
    """
    Adds Gaussian noise to numeric columns of the ml_df.
    :param noise_level: Standard deviation of the Gaussian noise relative to each feature's std.
    :param seed: Random seed for reproducibility.
    """
    np.random.seed(seed)
    numeric_cols = model.ml_df.select_dtypes(include=[np.number]).columns
    numeric_cols = [col for col in numeric_cols if col != ['phase', 'FCC', 'BCC', 'Other']]

    for col in numeric_cols:
        std_dev = model.ml_df[col].std()
        noise = np.random.normal(0, noise_level * std_dev, size=model.ml_df.shape[0])
        model.ml_df[col] += noise

    print(f"Added noise to {len(numeric_cols)} numerical columns.")

import matplotlib.pyplot as plt
import numpy as np

def plot_noise_impact_filled(noise_levels, mean_accuracy, std_accuracy, title="Model Accuracy Under Noise"):
    """
    Plots model accuracy vs. noise level with shaded standard deviation.

    Parameters:
    - noise_levels: List or array of noise percentages (e.g., [0, 2, 5, 10, 15])
    - mean_accuracy: Mean accuracy at each noise level
    - std_accuracy: Standard deviation of accuracy at each noise level
    - title: Title of the plot (optional)
    """
    noise_levels = np.array(noise_levels)
    mean_accuracy = np.array(mean_accuracy)
    std_accuracy = np.array(std_accuracy)

    upper = mean_accuracy + std_accuracy
    lower = mean_accuracy - std_accuracy

    plt.figure(figsize=(8, 5))
    plt.plot(noise_levels, mean_accuracy, '-o', color='royalblue', linewidth=2, label='Mean Accuracy')
    plt.fill_between(noise_levels, lower, upper, color='royalblue', alpha=0.2, label='±1 SD')

    plt.title(title, fontsize=14)
    plt.xlabel('Noise Level (%)', fontsize=12)
    plt.ylabel('Mean Accuracy (%)', fontsize=12)
    plt.xticks(noise_levels)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.show()


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize
from scipy.stats import ks_2samp
import numpy as np
import matplotlib.pyplot as plt


def ks_plot_multiclass(model_obj, class_index=0, test_size=0.3, random_state=42):
    """
    Performs a Kolmogorov–Smirnov test and plots ECDFs for the target class probability.

    Parameters:
    - model_obj: instance of your Model class
    - class_index: index of the class (e.g., 0 for BCC, 1 for FCC, etc.)
    - test_size: train/test split ratio
    - random_state: reproducibility
    """
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import label_binarize
    from scipy.stats import ks_2samp
    import matplotlib.pyplot as plt
    import numpy as np

    X_train, X_test, y_train, y_test = train_test_split(
        model_obj.X, model_obj.y, test_size=test_size, random_state=random_state, stratify=model_obj.y
    )

    model_obj.model.fit(X_train, y_train.ravel())

    y_probs = model_obj.model.predict_proba(X_test)
    y_true_bin = label_binarize(y_test, classes=np.unique(model_obj.y))

    pred_probs = y_probs[:, class_index]
    actuals = y_true_bin[:, class_index]

    pos_probs = pred_probs[actuals == 1]
    neg_probs = pred_probs[actuals == 0]

    stat, p = ks_2samp(pos_probs, neg_probs)

    def ecdf(data):
        x = np.sort(data)
        y = np.arange(1, len(x) + 1) / len(x)
        return x, y

    x_pos, y_pos = ecdf(pos_probs)
    x_neg, y_neg = ecdf(neg_probs)

    # Plot settings
    plt.figure(figsize=(7, 7))  # square plot
    plt.step(x_pos, y_pos, label="Positive Class", color="blue")
    plt.step(x_neg, y_neg, label="Negative Class", color="orange")

    plt.title(f"K-S Test for Class {class_index}\nD = {stat:.3f}, p = {p:.3f}", fontsize=16)
    plt.xlabel("Predicted Probability", fontsize=14)
    plt.ylabel("Empirical CDF", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(fontsize=12)
    plt.tight_layout()
    plt.show()

    print(f"K-S Statistic: {stat:.4f}")
    print(f"P-value: {p:.4f}")


import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize

def evaluate_model_calibration(model_obj, test_size=0.7, random_state=42, n_bins=10):
    """
    Splits the data, fits the model if needed, and plots calibration curves
    for each class in a multiclass Model instance—using the actual class names.

    Parameters:
    - model_obj: an instance of your Model class (with .X, .y, .model)
    - test_size: fraction of data to hold out for testing
    - random_state: for reproducibility
    - n_bins: number of bins for the calibration curve
    """
    # 1. Split data
    X_train, X_test, y_train, y_test = train_test_split(
        model_obj.X, model_obj.y.ravel(),
        test_size=test_size,
        random_state=random_state,
        stratify=model_obj.y
    )

    # 2. Fit/re-fit model
    model = model_obj.model
    model.fit(X_train, y_train)

    # 3. Predict probabilities
    probs = model.predict_proba(X_test)
    class_labels = model.classes_  # e.g. ['BCC','FCC','Other'] or similar
    y_test_bin = label_binarize(y_test, classes=class_labels)

    # 4. Plot calibration curves and compute Brier scores
    plt.figure(figsize=(8, 6))
    for i, cls in enumerate(class_labels):
        true_i = y_test_bin[:, i]
        prob_i = probs[:, i]

        # calibration curve
        frac_pos, mean_pred = calibration_curve(true_i, prob_i,
                                                n_bins=n_bins,
                                                strategy='uniform')

        plt.plot(mean_pred, frac_pos, marker='o', label=f"{cls}")
        bs = brier_score_loss(true_i, prob_i)
        print(f"Brier score for class '{cls}': {bs:.4f}")

    # 5. Perfect calibration line
    plt.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
    plt.title("Calibration Curves by Class")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


from scipy.stats import ks_2samp
import pandas as pd

from scipy.stats import ks_2samp
import pandas as pd


def run_ks_test_on_model_features(model_instance, test_df=None):
    """
    Runs Kolmogorov–Smirnov test for all input features between the training and test datasets of the given model.
    """
    if test_df is None:
        # Use get_train_test_split to get arrays
        X_train_array, X_test_array, _, _ = dc.get_train_test_split(model_instance.ml_df, model_instance.x_columns,
                                                                    model_instance.y_column)

        # Convert arrays to DataFrames using column names
        X_train = pd.DataFrame(X_train_array, columns=model_instance.x_columns)
        X_test = pd.DataFrame(X_test_array, columns=model_instance.x_columns)
    else:
        # Ensure test_df has the expected structure
        X_test = test_df[model_instance.x_columns].dropna()
        X_train = model_instance.train_df[model_instance.x_columns].dropna()

    results = []

    for feature in model_instance.x_columns:
        train_values = X_train[feature].dropna()
        test_values = X_test[feature].dropna()

        ks_stat, p_value = ks_2samp(train_values, test_values)

        results.append({
            'Feature': feature,
            'KS Statistic': ks_stat,
            'P-Value': p_value,
            'Distribution Stable': p_value > 0.05
        })

    ks_df = pd.DataFrame(results)
    print(ks_df.sort_values(by='KS Statistic', ascending=False))
    return ks_df


if __name__ == '__main__':
    model = Model(model_type='xgb', y_column='phase', thermo_fields=True,
                  file_loc='..\cep-tables\Empirical_data_combined.csv', feature_selection='elliot')
    ks_plot_multiclass(model, class_index=2)