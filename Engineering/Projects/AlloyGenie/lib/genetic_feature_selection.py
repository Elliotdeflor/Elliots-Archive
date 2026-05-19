from model_class import *
import numpy as np
import random
import pandas as pd
from deap import base, creator, tools, algorithms
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, r2_score


class GeneticFeatureSelector:
    def __init__(self, X, y, selected_features=None, n_gen=20, pop_size=10):
        if selected_features is not None:
            self.X = X[selected_features]
            self.features = selected_features
        else:
            self.X = X
            self.features = list(X.columns)

        self.y = np.ravel(y)
        self.n_gen = n_gen
        self.pop_size = pop_size
        self.n_features = len(self.features)
        self.best_features = []

        # Determine if y is categorical (classification) or continuous (regression)
        self.is_classification = np.issubdtype(y.dtype, np.integer) and len(np.unique(y)) < 20  # Threshold for classification

        # Define fitness function type (maximize accuracy for classification, R² for regression)
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self.toolbox.register("individual", self.init_individual)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
        self.toolbox.register("evaluate", self.eval_individual)

    def init_individual(self):
        return creator.Individual([random.randint(0, 1) for _ in range(self.n_features)])

    def eval_individual(self, individual):
        if sum(individual) == 0:
            return 0.0,

        selected_features = [self.features[i] for i in range(self.n_features) if individual[i] == 1]
        X_selected = self.X[selected_features]
        X_train, X_test, y_train, y_test = train_test_split(X_selected, self.y, test_size=0.3, random_state=42)

        if self.is_classification:
            model = RandomForestClassifier(n_estimators=50, random_state=42)
            model.fit(np.array(X_train), y_train)
            y_pred = model.predict(np.array(X_test))
            return accuracy_score(y_test, y_pred),
        else:
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(np.array(X_train), y_train)
            y_pred = model.predict(np.array(X_test))
            return r2_score(y_test, y_pred),  # R² score for regression

    def run(self):
        population = self.toolbox.population(n=self.pop_size)
        algorithms.eaSimple(population, self.toolbox, cxpb=0.5, mutpb=0.2, ngen=self.n_gen,
                            stats=None, halloffame=None, verbose=True)

        best_individual = tools.selBest(population, k=1)[0]
        self.best_features = [self.features[i] for i in range(self.n_features) if best_individual[i] == 1]

        print("Selected Features:", self.best_features)
        return self.best_features

    def get_selected_data(self):
        return self.X[self.best_features], self.y


if __name__ == "__main__":
    model = Model()
    selector = GeneticFeatureSelector(model.X, model.y)
    selected_columns = selector.run()
    filtered_data = selector.get_selected_data()
    print(filtered_data)
