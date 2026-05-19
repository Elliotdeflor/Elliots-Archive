import numpy as np
import random
from deap import base, creator, tools, algorithms
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from model_class import *


def evaluate(individual, X, y, model_type, task_type, cv=5):
    y = np.ravel(y)  # Ensure y is 1D

    if model_type == 'rf':
        params = {
            'n_estimators': max(1, int(individual[0])),
            'max_depth': int(individual[1]) if individual[1] > 0 else None,
            'min_samples_split': max(2, int(individual[2]))
        }
        model = RandomForestClassifier(**params) if task_type == 'classification' else RandomForestRegressor(**params)
    elif model_type == 'xgb':
        params = {
            'n_estimators': max(1, int(individual[0])),
            'max_depth': int(individual[1]) if individual[1] > 0 else None,
            'learning_rate': max(0.01, min(individual[2], 0.3))
        }
        model = XGBClassifier(**params) if task_type == 'classification' else XGBRegressor(**params)
    elif model_type == 'mlp':
        params = {
            'hidden_layer_sizes': (max(32, min(int(individual[0]), 128)),
                                   max(16, min(int(individual[1]), 64)),
                                   max(8, min(int(individual[2]), 32))),
            'alpha': max(1e-5, min(individual[3], 1e-1)),
            'learning_rate_init': max(0.001, min(individual[4], 0.1)),
            'max_iter': 500
        }
        model = MLPClassifier(**params) if task_type == 'classification' else MLPRegressor(**params)

    scores = cross_val_score(model, X, y, cv=cv,
                             scoring='accuracy' if task_type == 'classification' else 'neg_mean_squared_error')
    return scores.mean(),


def grid_search_hyperparameter_optimization(X, y, y_column, model_type='rf', cv=2):
    if y_column == 'phase':
        task_type = 'classification'
    else:
        task_type = 'regression'
    y = np.ravel(y)  # Ensure y is 1D

    param_grid = {}
    if model_type == 'rf':
        param_grid = {
            'n_estimators': [10, 50, 100, 200],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5, 10]
        }
        model = RandomForestClassifier() if task_type == 'classification' else RandomForestRegressor()
    elif model_type == 'xgb':
        param_grid = {
            'n_estimators': [10, 50, 100, 200],
            'max_depth': [3, 6, 9],
            'learning_rate': [0.01, 0.1, 0.2]
        }
        model = XGBClassifier() if task_type == 'classification' else XGBRegressor()
    elif model_type == 'mlp':
        param_grid = {
            'hidden_layer_sizes': [(32, 16, 8), (64, 32, 16), (128, 64, 32)],
            'alpha': [1e-5, 1e-3, 1e-1],
            'learning_rate_init': [0.001, 0.01, 0.1]
        }
        model = MLPClassifier(max_iter=500) if task_type == 'classification' else MLPRegressor(max_iter=500)

    grid_search = GridSearchCV(model, param_grid, cv=cv,
                               scoring='accuracy' if task_type == 'classification' else 'neg_mean_squared_error')
    grid_search.fit(X, y)

    print(f"Best parameters for {model_type}: {grid_search.best_params_}")
    return grid_search.best_params_


if __name__ == '__main__':
    model = Model(model_type='rf')
    print(grid_search_hyperparameter_optimization(model.X, model.y, model.y_column, model_type=model.model_type))
