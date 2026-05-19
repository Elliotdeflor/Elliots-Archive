from datetime import datetime

import numpy as np
import pandas as pd
from sklearn import feature_selection

import data_cleansing as dc
import generate_thermodynamic_fields as gtf
import mlp_models as mlp
import random_forest_models as rf
import xgb_models as xgb
from elliot_feature_selection import *
from genetic_feature_selection import *
from bayes_search_hp import *
from genetic_algorithm_hp import *
from grid_search_hp import *
from data_visualisation import *

class Model():
    def __init__(self, x_columns=None, thermo_fields=False, feature_selection=None, y_column='phase', file_loc=r'..\mat-data.csv', model_type='xgb', fill=False, params=None, hp_optimisation=None):
        self.fill = fill
        self.feature_selection = feature_selection
        self.params = params
        if x_columns == None:
            file = pd.read_csv(file_loc)
            x_columns = file.columns
        features = np.array(x_columns)
        # String to check and remove
        remove_str = y_column
        # Remove the string if it exists
        filtered_features = np.array([f for f in features if f != remove_str])
        x_columns = list(filtered_features)
        if thermo_fields == True:
            x_columns += ["VEC", "atomic_mixing_entropy", "atomic_size_difference", "electronegativity_difference"]

        self.unfiltered_x_cols = x_columns
        self.x_columns = x_columns
        self.y_column = y_column
        self.model_type = model_type
        self.file_loc = file_loc
        self.file_df = pd.read_csv(file_loc)
        self.ml_df = self.create_ml_df()
        self.X, self.y = dc.get_x_and_y(self.ml_df, self.x_columns, self.y_column)
        if feature_selection == 'elliot':
            self.run_elliot_fs()
        if feature_selection == 'genetic':
            self.run_genetic_fs()
        self.model = self.create_model()
        if hp_optimisation == 'bayesian':
            print("Running bayes hyperparameter optimization")
            self.params = bayesian_optimization(model_type=model_type, X=self.X, y=np.ravel(self.y))
            optimised_model = self.create_model()
            self.model = optimised_model
        elif hp_optimisation == 'genetic':
            print("Running genetic hyperparameter optimization")
            self.params = genetic_hyperparameter_optimization(self.X,self.y, self.y_column, model_type=self.model_type)
            optimised_model = self.create_model()
            self.model = optimised_model
        elif hp_optimisation == 'grid':
            print("Running grid search hyperparameter optimization")
            self.params = grid_search_hyperparameter_optimization(self.X, self.y, self.y_column, model_type=self.model_type)
            print(self.params)
            optimised_model = self.create_model()
            self.model = optimised_model

    def run_elliot_fs(self):
        print("Running elliot fs")
        elliotfs = ElliotFeatureSelection(n_iter=50, random_state=42, std_threshold=-1)
        if self.y_column == 'phase':
            columns = [str(col) for col in self.ml_df.columns if col not in ['phase', 'BCC', 'FCC', 'Other']]
        else:
            columns = [str(col) for col in self.ml_df.columns if col != self.y_column]
        X = pd.DataFrame(self.X, columns=columns, )
        elliotfs.fit(X, self.y.ravel())
        self.x_columns = elliotfs.selected_features
        print("Elliot's algorithm chose selected features: ", self.x_columns)

    def run_genetic_fs(self):
        print("Running genetic fs")
        columns = (dc.create_training_dataframe_struc(self.x_columns).columns).astype(str)
        X = pd.DataFrame(self.X, columns=columns)
        selector = GeneticFeatureSelector(X, self.y.squeeze())  # Replace "target" with actual target column name
        columns = selector.run()
        columns = dc.get_elements() + columns
        self.x_columns = columns
        print("Genetic algorithm selected the following features: ", columns)

    def create_ml_df(self):
        columns = self.unfiltered_x_cols + [self.y_column]
        print(columns)
        features = np.array(columns)
        # List of elements to remove
        omit_list = {"VEC", "atomic_mixing_entropy", "atomic_size_difference", "electronegativity_difference"}

        # Filtered array (removes elements in omit_list)
        filtered_features = np.array([f for f in features if f not in omit_list])
        self.file_df = self.file_df[filtered_features]
        df = dc.create_training_dataframe(self.file_df, filtered_features)
        if len(features) != len(filtered_features):
            df = gtf.add_thermodynamic_properties(df)
            thermodynamic_fields = df[list(omit_list)]
            self.file_df[thermodynamic_fields.columns] = thermodynamic_fields
        return df

    def create_model(self):
        try:
            columns = self.x_columns + [self.y_column]
            if self.feature_selection == None:
                train_df = dc.create_training_dataframe(self.file_df, columns)
            else:
                train_df = self.ml_df[columns]
        except:
            columns = self.x_columns + dc.get_phases()
            if self.feature_selection == None:
                train_df = dc.create_training_dataframe(self.file_df, columns)
            else:
                train_df = self.ml_df[columns]
        print(train_df)
        print("training df columns:", len(train_df.columns))
        match self.model_type:
            case 'xgb':
                if self.params is None:
                    model, score = xgb.create_xgb_model(train_df, self.x_columns, self.y_column, fill=self.fill)
                else:
                    model, score = xgb.create_xgb_model(train_df, self.x_columns, self.y_column, fill=self.fill,
                                                 params=self.params)
            case 'mlp':
                if self.params is None:
                    model, score = mlp.create_mlp_model(train_df, self.x_columns, self.y_column, fill=self.fill)
                else:
                    model, score = mlp.create_mlp_model(train_df, self.x_columns, self.y_column, fill=self.fill,
                                                 params=self.params)
            case 'rf':
                if self.params is None:
                    model, score = rf.create_random_forest_model(train_df, self.x_columns, self.y_column, fill=self.fill)
                else:
                    model, score = rf.create_random_forest_model(train_df, self.x_columns, self.y_column, fill=self.fill,
                                                          params=self.params)
        self.test_score = score
        self.train_df = train_df
        return model




if __name__ == '__main__':
    #model1 = Model(model_type='xgb', thermo_fields=True, y_column='phase', file_loc=r'..\cep-tables\HEA_big_dataset.csv')
    #model2 = Model(model_type='xgb', thermo_fields=True, y_column='phase', file_loc=r'..\cep-tables\MPEA_dataset.csv')
    #model3 = Model(model_type='xgb', thermo_fields=True, y_column='phase', file_loc=r'..\cep-tables\mat-data.csv')
    #X_train, X_test, y_train, y_test = dc.get_train_test_split(model3.ml_df, model3.x_columns, model3.y_column)
    #model3.model.fit(model1.X,model1.y)
    #X_train = np.concatenate((X_train, model2.X), axis=0)
    #y_train = np.concatenate((y_train, model2.y), axis=0)

    #model2.model.fit(X_train, y_train.ravel())

    #rf.evaluate_classification_model(model2.model, X_train, y_train)
    #rf.evaluate_classification_model(model2.model, X_test, y_test)
    #model2 = Model(model_type='xgb', x_columns=['composition'], thermo_fields=True, file_loc=r'..\meta\hea_big_dataset.csv', y_column='phase')
    #model = Model(file_loc=r'..\cep-tables\Empirical_data_combined.csv', hp_optimisation='grid')
    model = Model()
    df = model.train_df
    #df.to_csv('train_df.csv')
    print(model.train_df.head)
    #print("accuracy on test set")
    #evaluate_classification_model(model.model, model2.X, model2.y)
    #print("total accuracy")
    #evaluate_classificmation_model(model.model, model.X, model.y)
