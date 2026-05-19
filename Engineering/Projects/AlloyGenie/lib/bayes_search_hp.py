from skopt import BayesSearchCV
from skopt.space import Real, Integer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from xgboost import XGBClassifier, XGBRegressor
from sklearn.base import BaseEstimator
import numpy as np
from sklearn.utils.multiclass import type_of_target
from model_class import *
from sklearn.preprocessing import LabelEncoder

# MLPWrapper with correctly formatted parameters
class MLPWrapper(BaseEstimator):
    def __init__(self, layer1=32, layer2=32, layer3=32, alpha=1e-4, learning_rate_init=0.001, is_classification=True):
        self.layer1 = layer1
        self.layer2 = layer2
        self.layer3 = layer3
        self.alpha = alpha
        self.learning_rate_init = learning_rate_init
        self.is_classification = is_classification

    def fit(self, X, y):
        model_class = MLPClassifier if self.is_classification else MLPRegressor
        self.model = model_class(
            hidden_layer_sizes=(self.layer1, self.layer2, self.layer3),  # Ensure correct tuple formatting
            alpha=self.alpha,
            learning_rate_init=self.learning_rate_init,
            max_iter=2500
        )
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)

    def score(self, X, y):
        return self.model.score(X, y)


def get_param_space(model_type):
    """
    Returns the hyperparameter search space for a given model type.
    """
    param_spaces = {
        "rf": {
            'n_estimators': Integer(50, 500),
            'max_depth': Integer(3, 20),
            'min_samples_split': Integer(2, 10),
            'min_samples_leaf': Integer(1, 10)
        },
        "mlp": {
            'layer1': Integer(32, 128),
            'layer2': Integer(16, 64),
            'layer3': Integer(8, 32),
            'alpha': Real(1e-5, 1e-1, prior='log-uniform'),
            'learning_rate_init': Real(0.001, 0.1, prior='log-uniform')
        },
        "xgb": {
            'learning_rate': Real(0.01, 0.3, prior='log-uniform'),
            'n_estimators': Integer(50, 500),
            'max_depth': Integer(3, 10),
            'subsample': Real(0.5, 1.0),
            'colsample_bytree': Real(0.5, 1.0)
        }
    }
    return param_spaces.get(model_type, None)


def get_model(model_type, is_classification):
    """
    Returns the appropriate model (classifier or regressor) based on the task.
    """
    if model_type == "rf":
        return RandomForestClassifier(n_jobs=-1) if is_classification else RandomForestRegressor(n_jobs=-1)
    elif model_type == "mlp":
        return MLPWrapper(is_classification=is_classification)
    elif model_type == "xgb":
        return XGBClassifier(eval_metric='logloss', n_jobs=-1) if is_classification else XGBRegressor(n_jobs=-1)
    return None


import numpy as np
from sklearn.utils.multiclass import type_of_target


def is_classification_task(y):
    """Determines if the task is classification (discrete labels) or regression (continuous values)."""
    target_type = type_of_target(y)

    # Classification tasks
    if target_type in ["binary", "multiclass"]:
        return True

    # Ensure y is a NumPy array
    y = np.asarray(y)

    # If y contains float values, it's regression
    if np.issubdtype(y.dtype, np.floating):
        return False  # Regression

    # If y contains many unique values, it's likely regression
    unique_values = len(np.unique(y))
    if unique_values > 20:  # Arbitrary threshold, can be tuned
        return False  # Regression

    return True  # Default case (classification)


def bayesian_optimization(model_type, X, y, cv=5, n_iter=50, random_state=None):
    is_classification = is_classification_task(y)
    scoring = 'accuracy' if is_classification else 'r2'

    model = get_model(model_type, is_classification)
    param_space = get_param_space(model_type)

    if model is None or param_space is None:
        raise ValueError("Unsupported model type. Choose from 'rf', 'mlp', or 'xgb'.")

    # Ensure y is 1D
    y = np.asarray(y).ravel()

    # Apply LabelEncoder only if classification
    if is_classification:
        encoder = LabelEncoder()
        y = encoder.fit_transform(y)
    try:
        if is_classification:
            encode = LabelEncoder()
            y = encode.fit_transform(y)
        bayes_search = BayesSearchCV(
            model,
            param_space,
            n_iter=n_iter,
            cv=cv,
            scoring=scoring,
            random_state=random_state,
            n_jobs=-1
        )

        bayes_search.fit(X, y)
    except:
        scoring = 'accuracy' if not is_classification else 'r2'
        model = get_model(model_type, not is_classification)
        bayes_search = BayesSearchCV(
            model,
            param_space,
            n_iter=n_iter,
            cv=cv,
            scoring=scoring,
            random_state=random_state,
            n_jobs=-1
        )

        bayes_search.fit(X, y)

    best_params = bayes_search.best_params_

    # Ensure correct format for MLP model
    if model_type == "mlp":
        formatted_params = {
            'hidden_layer_sizes': (best_params['layer1'], best_params['layer2'], best_params['layer3']),
            'alpha': best_params['alpha'],
            'learning_rate_init': best_params['learning_rate_init'],
        }
    else:
        formatted_params = best_params

    print(f"Optimized parameters: {formatted_params}")
    return formatted_params



if __name__ == '__main__':
    model_class = Model(model_type='xgb', x_columns=['composition','density'], thermo_fields=True, y_column='young_modulus', feature_selection='genetic', hp_optimisation='bayesian')
