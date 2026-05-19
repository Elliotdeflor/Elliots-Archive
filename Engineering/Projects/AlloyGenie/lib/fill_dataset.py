import pandas as pd
from model_class import *
import os
import multiprocessing
import sys

def get_hp_optimisations():
    return ['bayesian', None]

def get_feature_selections():
    return ['genetic', None]

def get_thermo_fields():
    return [True, False]
def get_null_fields(file_loc):
    df = pd.read_csv(file_loc)
    return df.columns[df.isnull().any()].tolist()

def get_non_empty_fields(file_loc):
    df = pd.read_csv(file_loc)
    return df.columns[df.notna().all()].tolist()


import multiprocessing
import pandas as pd
import os
from model_class import *

def safe_join(process, timeout=1):
    """
    Attempts to join the process within a timeout.
    If it fails, the process is terminated.
    """
    print(f"Joining process {process.pid}...")
    process.join(timeout)
    if process.is_alive():
        print(f"Process {process.pid} did not finish in time. Terminating...")
        process.terminate()
        process.join()  # Ensure it's fully cleaned up
        print(f"Process {process.pid} terminated.")
    else:
        print(f"Process {process.pid} joined successfully.")
def model_wrapper(y_column, feature_selection, hp_optimisation, model_type, thermo_fields ,rmse, model):
    """Wraps the model output in the expected format."""
    return {
        'y_column': y_column,
        'feature_selection': feature_selection,
        'hp_optimisation': hp_optimisation,
        'model_type': model_type,
        'thermo_fields': thermo_fields,
        'rmse': rmse,
        'model':model
    }


def create_and_evaluate_model(model_config, queue):
    """Trains and evaluates a model, then puts the result in the queue."""
    model_type, x_columns, y_column, thermo_fields, file_loc, feature_selection, hp_optimisation, params = model_config

    # Suppress print output
    with open(os.devnull, 'w') as fnull:
        old_stdout = sys.stdout
        try:
            sys.stdout = fnull  # Redirect stdout to null (hide prints)

            # Instantiate and train the model (Assuming Model class exists)
            model = Model(model_type=model_type,
                          x_columns=x_columns,
                          y_column=y_column,
                          thermo_fields=thermo_fields,
                          file_loc=file_loc,
                          feature_selection=feature_selection,
                          hp_optimisation=hp_optimisation,
                          params=params)

            # Get model performance (assuming test_score gives RMSE)
            rmse = model.test_score

            # Wrap result
            result = model_wrapper(y_column, feature_selection, hp_optimisation, model_type, thermo_fields, rmse, model)

        finally:
            sys.stdout = old_stdout  # Restore stdout

    # Store result in the queue (outside print suppression block)
    queue.put(result)


def get_best_model_light(new_file_loc, null_columns, non_empty_columns):
    x_columns = non_empty_columns
    y_columns = [col for col in null_columns if col != 'phase']

    model_types = ['xgb', 'mlp', 'rf']
    model_configs = [(model_type, x_columns, y_column, False, new_file_loc, None, None, None)
                     for y_column in y_columns for model_type in model_types]

    print(f'Selecting optimal model... {len(model_configs)} configurations to test')

    queue = multiprocessing.Queue()
    processes = []

    for config in model_configs:
        process = multiprocessing.Process(target=create_and_evaluate_model, args=(config, queue))
        processes.append(process)
        process.start()

    results = []
    for i in range(len(processes)):
        results.append(queue.get())  # Retrieve result from the queue
    for process in processes:
        safe_join(process)

    best_model = min(results, key=lambda x: x['rmse'])
    print("Best Model and y_column:", best_model)
    print("testing feature selection and hp optimisation...")

    hp_optimisations = get_hp_optimisations()
    feature_selections = get_feature_selections()
    thermo_fieldss = get_thermo_fields()

    model_configs = [(best_model['model_type'], x_columns, best_model['y_column'], thermo_fields, new_file_loc,
                      feature_selection, hp_optimisation, None)
                     for thermo_fields in thermo_fieldss for feature_selection
                     in feature_selections for hp_optimisation in hp_optimisations]

    print(f'Refining model... {len(model_configs)} configurations to test')

    processes = []

    for config in model_configs:
        process = multiprocessing.Process(target=create_and_evaluate_model, args=(config, queue))
        processes.append(process)
        process.start()
          # Retrieve results before joining
    results = []
    for i in range(len(processes)):
        results.append(queue.get())

    for process in processes:
        safe_join(process, timeout=10)
    print("Optimization complete!")
    best_model = min(results, key=lambda x: x['rmse'])
    print("Best Model After Optimization:", best_model)


    return best_model   # Return results if needed




def get_best_model_ultra(new_file_loc):
    null_columns=get_null_fields(new_file_loc)
    non_empty_columns=get_non_empty_fields(new_file_loc)
    x_columns= non_empty_columns
    y_columns = null_columns
    y_columns = [item for item in y_columns if item != 'phase']
    model_types = ['xgb','mlp','rf']
    hp_optimisations = ['bayesian', None]
    feature_selections = ['genetic', None]
    thermo_fieldss = [True, False]
    model_configs = []
    for model_type in model_types:
        for hp_optimisation in hp_optimisations:
            for feature_selection in feature_selections:
                for thermo_fields in thermo_fieldss:
                    for y_column in y_columns:
                        model_config = model_type, x_columns, y_column, thermo_fields, new_file_loc, feature_selection, hp_optimisation
                        model_configs.append(model_config)
    print('number of test models:', len(model_configs))
    processes = []
    iter = 0
    for config in model_configs:
        iter += 1
        # Create a new process for each model and start it
        sys.stdout = open(os.devnull, 'w')
        process = multiprocessing.Process(target=create_and_evaluate_model, args=(config,))
        processes.append(process)
        process.start()
        sys.stdout = sys.__stdout__
        print("test class {} created with config: {}".format(iter, config))
        sys.stdout = open(os.devnull, 'w')
    for process in processes:
        process.join()
        print(process.test_score)

    # multiproccessing create a version of each
    return processes

def init_filled_file(file_loc):
    filename = os.path.basename(file_loc)
    file_old = pd.read_csv(file_loc)
    file_old.to_csv(r'..\cep-tables\{}'.format(filename), index=False)
    return r'..\cep-tables\{}'.format(filename)


def fill_missing_values(new_file_loc, model_lib):
    model = model_lib['model']
    target_column = model_lib['y_column']
    file = pd.read_csv(new_file_loc)
    model.file_df = file
    columns = model.x_columns + [model.y_column]
    ml_df = model.create_ml_df()
    if model.feature_selection == None:
        columns = (dc.create_training_dataframe_struc(columns)).columns
    train_df = ml_df[columns]
    df_filled = train_df.copy()

    # Identify rows with missing target values
    missing_mask = df_filled[target_column].isnull()

    if not missing_mask.any():
        print(f"No missing values found in '{target_column}'.")
        return file

    # Extract features for prediction
    x_columns = [col for col in columns if col != target_column]
    X_missing = df_filled.loc[missing_mask, x_columns]

    # Convert to NumPy array for efficiency
    X_missing_np = X_missing.to_numpy()

    # Predict missing values in batches
    batch_size = 5000  # Adjust based on memory availability
    predicted_values = []

    for i in range(0, len(X_missing_np), batch_size):
        batch = X_missing_np[i:i + batch_size]
        predicted_values.extend(model.model.predict(batch))

    # Fill missing values
    df_filled.loc[missing_mask, target_column] = predicted_values

    # Save only updated values
    file[target_column] = df_filled[target_column]

    print(f"Filled {len(predicted_values)} missing values in '{target_column}'.")
    return file


def fill_table(file_loc, y_column, training_table_loc=None):
    stack = []
    new_file_loc = init_filled_file(file_loc)
    null_columns = get_null_fields(new_file_loc)
    null_columns.remove(y_column)
    non_empty_columns = get_non_empty_fields(new_file_loc)
    print('Filling columns:', null_columns)
    while len(null_columns) > 0:
        if training_table_loc == None:
            model_lib = get_best_model_light(new_file_loc, null_columns, non_empty_columns)
            df_filled = fill_missing_values(new_file_loc, model_lib)
            df_filled.to_csv(new_file_loc, index=None)
        else:
            model_lib = get_best_model_light(training_table_loc, null_columns, non_empty_columns)
            df_filled = fill_missing_values(new_file_loc, model_lib)
            df_filled.to_csv(new_file_loc, index=None)
        filled_col = model_lib['y_column']
        null_columns = [col for col in null_columns if col != filled_col]
        non_empty_columns.append(filled_col)
        stack.append(model_lib)
    return stack







if __name__ == '__main__':
    fill_table(r'..\cep-tables\HEA_big_dataset.csv','phase', training_table_loc=r'..\cep-tables\Empirical_data_combined.csv')
