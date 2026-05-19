
import data_cleansing as dc

from sklearn.neural_network import MLPRegressor
import numpy as np

from sklearn.metrics import accuracy_score
from sklearn.metrics import mean_squared_error
from sklearn.neural_network import MLPClassifier

def train_neural_network_classifier(X_train, y_train, params):
    """
    Train a neural network classifier using scikit-learn's MLPClassifier.

    Parameters:
    - X_train: DataFrame or array-like, shape (n_samples, n_features), training features
    - y_train: Series or array-like, shape (n_samples,), target class labels
    - hidden_layer_sizes: tuple, number of neurons in each hidden layer (default (100,))
    - activation: str, activation function ('identity', 'logistic', 'tanh', 'relu') (default 'relu')
    - solver: str, optimizer ('lbfgs', 'sgd', 'adam') (default 'adam')
    - learning_rate: float, learning rate for optimization (default 0.001)
    - max_iter: int, maximum number of iterations for training (default 200)
    - random_state: int, seed for reproducibility (default 42)

    Returns:
    - model: Trained MLPClassifier model
    """
    # Initialize the model
    model = MLPClassifier(**params)

    # Train the model
    model.fit(X_train, y_train)

    return model

def train_neural_network_regressor(X_train, y_train, params):
    """
    Train a neural network regressor using scikit-learn's MLPRegressor.

    Parameters:
    - X_train: DataFrame or array-like, shape (n_samples, n_features), training features
    - y_train: Series or array-like, shape (n_samples,), target values
    - hidden_layer_sizes: tuple, number of neurons in each hidden layer (default (100,))
    - activation: str, activation function ('identity', 'logistic', 'tanh', 'relu') (default 'relu')
    - solver: str, optimizer ('lbfgs', 'sgd', 'adam') (default 'adam')
    - learning_rate: float, learning rate for optimization (default 0.001)
    - max_iter: int, maximum number of iterations for training (default 200)
    - random_state: int, seed for reproducibility (default 42)

    Returns:
    - model: Trained MLPRegressor model
    """
    # Initialize the model
    model = MLPRegressor(**params)


    # Train the model
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
    return y_pred

def create_mlp_model(df, x_columns, y_column, fill=False, params = {'hidden_layer_sizes':(100,),
                                   'activation':'relu',
                                   'solver':'adam',
                                   'learning_rate_init':0.001,
                                   'max_iter':10000,
                                   'random_state':42}):
    columns = []
    columns += x_columns
    columns.append(y_column)

    if fill == False:
        df = dc.get_all_not_null(df)
    print('number of entries:', df.shape[0])
    X_train, X_test, y_train, y_test = dc.get_train_test_split(df, x_columns, y_column)
    y_train = y_train.ravel()
    y_test = y_test.ravel()
    if y_column == 'phase':
        print("Building mlp phase classifier...")
        model = train_neural_network_classifier(X_train, y_train, params=params)
        accuracy = evaluate_classification_model(model, X_test, y_test)
        return model, accuracy
    elif isinstance(df[y_column].iloc[0], float):
        print("Building mlp regressor model...")
        model = train_neural_network_regressor(X_train, y_train, params=params)
        rmse = evaluate_regression_model(model, X_test, y_test)

        return model, rmse
    else:
        print("y value is not accepted")

if __name__ == '__main__':
    df = dc.get_core_data()
    print(df.head())
    params = {'hidden_layer_sizes':(256,128,16),
                                   'activation':'relu',
                                   'solver':'adam',
                                   'learning_rate_init':0.001,
                                   'max_iter':10000,
                                   'random_state':42}
    model = create_mlp_model(df, ['composition'], 'phase', params=params)
