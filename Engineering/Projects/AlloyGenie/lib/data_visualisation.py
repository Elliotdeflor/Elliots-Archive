import pandas as pd

from model_class import *
import matplotlib.pyplot as plt


def plot_regression_predictions(modelclass, title="Predicted vs True Values"):
    X = modelclass.X
    y = modelclass.y
    model = modelclass.model
    """
    Plots true values (y) against predicted values (y_pred) for a regression model.

    Parameters:
    - model: Trained regression model
    - X: DataFrame or array-like, input features
    - y: Series or array-like, true target values
    - title: str, optional, title of the plot

    Returns:
    - None
    """
    # Predict values
    y_pred = model.predict(X)

    # Create scatter plot
    plt.figure(figsize=(8, 8))
    plt.scatter(y, y_pred, alpha=0.6, color='blue', edgecolor='k', label="Predictions")
    plt.plot([min(y), max(y)], [min(y), max(y)], 'r--', lw=2, label="Ideal Line (y = y_pred)")
    plt.xlabel("True Values")
    plt.ylabel("Predicted Values")
    plt.title(title)
    plt.legend()
    plt.grid(alpha=0.4)
    plt.show()


import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix


def plot_classification_performance(modelclass, title="Confusion Matrix"):
    """
    Plots the confusion matrix for a classification model.

    Parameters:
    - model: Trained classification model
    - X: DataFrame or array-like, input features
    - y: Series or array-like, true target values
    - title: str, optional, title of the plot

    Returns:
    - None
    """
    # Predict class labels
    X = modelclass.X
    y=modelclass.y
    model=modelclass.model
    y_pred = model.predict(X)

    # Compute confusion matrix
    cm = confusion_matrix(y, y_pred)

    # Plot confusion matrix using sklearn's visualization
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=model.classes_)
    disp.plot(cmap=plt.cm.Blues, values_format='d')
    plt.title(title)
    plt.show()


import matplotlib.pyplot as plt
import re
from collections import Counter


def plot_element_counts(compositions, title="Element Counts in Compositions"):
    """
    Plots a bar chart of the counts of each element appearing in an array of compositions.

    Parameters:
    - compositions: list of strings, array of element compositions (e.g., ['AlFeCo0.5', 'Al0.5CoTi', 'CuCrFe'])
    - title: str, optional, title for the plot

    Returns:
    - None
    """
    # Regular expression to extract elements (assumes elements start with an uppercase letter, optionally followed by lowercase)
    element_pattern = re.compile(r'[A-Z][a-z]*')

    # Extract and count elements from all compositions
    element_counts = Counter()
    for composition in compositions:
        elements = element_pattern.findall(composition)
        element_counts.update(elements)

    # Prepare data for plotting
    elements = list(element_counts.keys())
    counts = list(element_counts.values())

    # Create bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(elements, counts, color='skyblue', edgecolor='black')
    plt.xlabel("Elements")
    plt.ylabel("Counts")
    plt.title(title)
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

import matplotlib.pyplot as plt

def plot_not_null_counts(df, title="Non-Null Entry Counts Per Column"):
    """
    Plots a bar chart showing the count of non-null entries for each column in a DataFrame.

    Parameters:
    - df: pandas DataFrame, the input DataFrame
    - title: str, optional, title for the plot

    Returns:
    - None
    """
    # Count non-null entries for each column
    not_null_counts = df.notnull().sum()
    print(not_null_counts)
    # Create the bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(not_null_counts.index, not_null_counts.values, color='skyblue', edgecolor='black')
    plt.xlabel("Columns")
    plt.ylabel("Non-Null Count")
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def evaluate_regression_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print("Model RMSE on test Set:", rmse)

def evaluate_classification_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy on test set:", accuracy)


import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import seaborn as sns


def feature_importance_plot(model, task='classification', plot=True):

    importances = model.model.feature_importances_
    # Create importance matrix
    importance_df = pd.DataFrame({
        'Feature': [col for col in model.ml_df.columns if col not in ['phase', 'FCC', 'BCC','Other']],
        'Importance': importances
    }).sort_values(by='Importance', ascending=False).reset_index(drop=True)

    # Optional plot
    if plot:
        plt.figure(figsize=(10, 6))
        sns.barplot(data=importance_df.head(32), x='Importance', y='Feature')
        plt.title('Feature Importances')
        plt.tight_layout()
        plt.show()

    return importance_df



import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import math


def feature_importance_matrix(model, task='classification', plot=True, shape=None):
    """
    Displays a matrix-style heatmap of feature importances.

    Parameters:
    - model: Trained model with .model (e.g., RandomForest) and .ml_df
    - task: Optional task indicator, unused here
    - plot: Whether to show the heatmap
    - shape: Optional shape override (rows, cols). If None, auto-calculate.
    """
    # Extract feature names and importances
    features = [col for col in model.ml_df.columns if col not in ['phase', 'FCC', 'BCC', 'Other']]
    importances = model.model.feature_importances_

    # Build DataFrame
    importance_df = pd.DataFrame({
        'Feature': features,
        'Importance': importances
    }).sort_values(by='Importance', ascending=False).reset_index(drop=True)

    if plot:
        n_features = len(features)

        # Auto-calculate shape if not provided
        if shape is None:
            n_cols = math.ceil(math.sqrt(n_features))
            n_rows = math.ceil(n_features / n_cols)
        else:
            n_rows, n_cols = shape
            if n_rows * n_cols < n_features:
                raise ValueError(f"Provided shape {shape} is too small for {n_features} features.")

        # Pad arrays to fit the matrix shape
        pad_len = n_rows * n_cols - n_features
        padded_importances = np.append(importance_df['Importance'].values, [np.nan] * pad_len)
        padded_features = importance_df['Feature'].tolist() + [''] * pad_len

        # Reshape for heatmap
        importance_matrix = padded_importances.reshape((n_rows, n_cols))
        label_matrix = np.array(padded_features).reshape((n_rows, n_cols))

        # Plot heatmap
        plt.figure(figsize=(1.5 * n_cols, 1.2 * n_rows))
        sns.heatmap(importance_matrix, annot=label_matrix, fmt='', cmap='YlGnBu',
                    cbar_kws={'label': 'Feature Importance'}, linewidths=0.5, square=True)
        plt.title('Feature Importance Matrix')
        plt.xticks([])
        plt.yticks([])
        plt.tight_layout()
        plt.show()

    return importance_df


if __name__ == "__main__":
    model = Model(model_type='rf' ,file_loc=r'..\meta\MPEA_dataset.csv', thermo_fields=True)
    feature_importance_plot(model)