import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import mean_squared_error
import data_cleansing as dc
import numpy as np
import random

def xgb_phase_classifier(X_train, y_train, params):
    # Define parameters


    # Initialize and train model
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train)
    return model

def xgb_regressor(X_train, y_train, params):
    model = xgb.XGBRegressor(**params)

    # Train the model
    model.fit(
        X_train,
        y_train,  # Stop if validation error doesn't improve for 10 rounds
        verbose=True
    )

    return model

def evaluate_regression_model(model, X_test, y_test):
    y_pred = model.predict(np.array(X_test))
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print("Model RMSE on test Set:", rmse)
    return rmse

def evaluate_classification_model(model, X_test, y_test):
    y_pred = model.predict(np.array(X_test))
    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy on test set:", accuracy)
    return accuracy
def predict_phase(model, field, x_columns):
    pred_field = dc.get_training_field(field, x_columns)
    y_pred = dc.get_phases()[model.predict(pred_field)[0]] # predicting phase as index, selecting index from array of phases
    print("y_pred: ", y_pred)
    return y_pred

def create_xgb_model(df, x_columns, y_column, fill=False, params=None):
    columns = []
    columns += x_columns
    columns.append(y_column)
    if fill == False:
        df = dc.get_all_not_null(df)
    print('number of entries:', df.shape[0])
    X_train, X_test, y_train, y_test = dc.get_train_test_split(df, x_columns, y_column)
    print(y_train)
    if y_column == 'phase':
        if params is None:
            params = {
                'objective': 'multi:softmax',
                'num_class': 4,
                'eval_metric': 'mlogloss'
            }
        print("Building xgb phase classifier...")
        model = xgb_phase_classifier(X_train, y_train, params=params)
        accuracy = evaluate_classification_model(model, X_test, y_test)
        return model, accuracy
    elif isinstance(df[y_column].iloc[0], float):
        if params is None:
            params = {'objective': 'reg:squarederror',
             'eval_metric': 'rmse',
             'random_state': random.randint(0,400000)}
        print("Building xgb regressor model...")
        model = xgb_regressor(np.array(X_train), np.array(y_train), params=params)
        rmse = evaluate_regression_model(model, X_test, y_test)
        return model, rmse
    else:
        print("y value is not accepted")

if __name__ == '__main__':
    df = dc.get_core_data()
    print(df.head())
    model = create_xgb_model(df, ['composition'], 'phase')