from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score
from sklearn.metrics import mean_squared_error
import data_cleansing as dc
import numpy as np
import pandas as pd

def train_random_forest_regressor(X_train, y_train, params = {'n_estimators':100,
    'max_depth':None,
    'random_state':42}):
    """
    Train a Random Forest regressor on the given training data.

    Parameters:
    - X_train: DataFrame or array-like, shape (n_samples, n_features), training features
    - y_train: Series or array-like, shape (n_samples,), target values
    - n_estimators: int, number of trees in the forest (default 100)
    - max_depth: int or None, maximum depth of each tree (default None for no limit)
    - random_state: int, seed for reproducibility (default 42)

    Returns:
    - model: Trained Random Forest regressor model
    """
    # Initialize the model
    model = RandomForestRegressor(**params)
    # Train the model
    model.fit(X_train, y_train)

    return model
from sklearn.ensemble import RandomForestClassifier

def train_random_forest_classifier(X_train, y_train, params = {'n_estimators':100,
    'max_depth':None,
    'random_state':42}):

    """
    Train a Random Forest classifier on the given training data.

    Parameters:
    - X_train: DataFrame or array-like, shape (n_samples, n_features), training features
    - y_train: Series or array-like, shape (n_samples,), target values
    - n_estimators: int, number of trees in the forest (default 100)
    - max_depth: int or None, maximum depth of each tree (default None for no limit)
    - random_state: int, seed for reproducibility (default 42)

    Returns:
    - model: Trained Random Forest classifier model
    """
    # Initialize the model
    model = RandomForestClassifier(**params)
    # Train the model
    X_train = X_train
    model.fit(X_train, y_train)
    return model

def evaluate_regression_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print("Model RMSE on test Set:", rmse)
    return rmse
def evaluate_classification_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy on test set:", accuracy)
    return accuracy

def predict_phase(model, field, x_columns):
    pred_field = dc.get_training_field(field, x_columns)
    y_pred = dc.get_phases()[model.predict(pred_field)[0]] # predicting phase as index, selecting index from array of phases
    print("y_pred: ", y_pred)

def create_random_forest_model(ml_df, x_columns, y_column, fill=False, params = {'n_estimators':150,
    'max_depth':100,
    'random_state':8}):

    columns = []
    columns += x_columns
    columns.append(y_column)
    df = ml_df
    if fill == False:
        df = dc.get_all_not_null(df)
    print('number of entries:', df.shape[0])
    X_train, X_test, y_train, y_test = dc.get_train_test_split(df, x_columns, y_column)
    if y_column == 'phase':
        print("Building rf phase classifier...")
        model = train_random_forest_classifier(X_train, y_train, params)
        accuracy = evaluate_classification_model(model, X_test, y_test)
        return model, accuracy
    elif isinstance(df[y_column].iloc[0], float):
        print("Building rf regressor model...")
        model = train_random_forest_regressor(X_train, y_train, params)
        rmse = evaluate_regression_model(model, X_test, y_test)
        return model, rmse
    else:
        print("y value is not accepted")

if __name__ == '__main__':
    df = dc.get_core_data()
    params = {'n_estimators':100,
    'max_depth':None,
    'random_state':42}
    model = create_random_forest_model(df, ['composition'], 'phase')
