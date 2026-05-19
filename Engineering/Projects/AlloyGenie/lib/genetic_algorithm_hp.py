import numpy as np
import random
from deap import base, creator, tools, algorithms
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from model_class import *  # Assuming you have a Model class handling dataset loading

def evaluate(individual, X, y, model_type, task_type, cv=5):
    y = y.ravel()
    if model_type == 'rf':
        params = {
            'n_estimators': max(1, int(individual[0])),
            'max_depth': int(individual[1]) if individual[1] >= 1 else None,
            'min_samples_split': max(2, int(individual[2]))  # Fixed to ensure min_samples_split >= 2
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

def custom_mutate(individual, model_type, indpb):
    if model_type == 'mlp':
        individual[0] = random.randint(32, 128) if random.random() < indpb else individual[0]
        individual[1] = random.randint(16, 64) if random.random() < indpb else individual[1]
        individual[2] = random.randint(8, 32) if random.random() < indpb else individual[2]
        individual[3] += random.uniform(-0.01, 0.01) if random.random() < indpb else individual[3]
        individual[4] += random.uniform(-0.01, 0.01) if random.random() < indpb else individual[4]
        individual[3] = max(1e-5, min(individual[3], 1e-1))
        individual[4] = max(0.001, min(individual[4], 0.1))
    elif model_type == 'rf':
        individual[0] = random.randint(10, 200) if random.random() < indpb else individual[0]  # n_estimators
        individual[1] = random.randint(1, 20) if random.random() < indpb else individual[1]  # max_depth
        individual[2] = random.randint(2, 20) if random.random() < indpb else individual[2]  # min_samples_split
    elif model_type == 'xgb':
        individual[0] = random.randint(10, 200) if random.random() < indpb else individual[0]  # n_estimators
        individual[1] = random.randint(1, 20) if random.random() < indpb else individual[1]  # max_depth
        individual[2] += random.uniform(-0.05, 0.05) if random.random() < indpb else individual[2]  # learning_rate
        individual[2] = max(0.01, min(individual[2], 0.3))  # Ensure learning_rate stays in [0.01, 0.3]
    return individual,

def genetic_hyperparameter_optimization(X, y, y_column, model_type='rf',
                                        n_generations=20, population_size=10,
                                        mutation_rate=0.2, crossover_rate=0.5):
    task_type = 'classification' if y_column == 'phase' else 'regression'

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    if model_type == 'rf':
        toolbox.register("attr_n_estimators", random.randint, 10, 200)
        toolbox.register("attr_max_depth", random.randint, 1, 20)
        toolbox.register("attr_min_samples_split", random.randint, 2, 20)  # Fixed to start from 2
        toolbox.register("individual", tools.initCycle, creator.Individual,
                         (toolbox.attr_n_estimators, toolbox.attr_max_depth, toolbox.attr_min_samples_split), n=1)
    elif model_type == 'xgb':
        toolbox.register("attr_n_estimators", random.randint, 10, 200)
        toolbox.register("attr_max_depth", random.randint, 1, 20)
        toolbox.register("attr_learning_rate", random.uniform, 0.01, 0.3)
        toolbox.register("individual", tools.initCycle, creator.Individual,
                         (toolbox.attr_n_estimators, toolbox.attr_max_depth, toolbox.attr_learning_rate), n=1)
    elif model_type == 'mlp':
        toolbox.register("attr_layer1", random.randint, 32, 128)
        toolbox.register("attr_layer2", random.randint, 16, 64)
        toolbox.register("attr_layer3", random.randint, 8, 32)
        toolbox.register("attr_alpha", random.uniform, 1e-5, 1e-1)
        toolbox.register("attr_learning_rate_init", random.uniform, 0.001, 0.1)
        toolbox.register("individual", tools.initCycle, creator.Individual,
                         (toolbox.attr_layer1, toolbox.attr_layer2, toolbox.attr_layer3, toolbox.attr_alpha,
                          toolbox.attr_learning_rate_init), n=1)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluate, X=X, y=y, model_type=model_type, task_type=task_type)
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", custom_mutate, model_type=model_type, indpb=mutation_rate)
    toolbox.register("select", tools.selTournament, tournsize=3)

    population = toolbox.population(n=population_size)

    algorithms.eaSimple(population, toolbox, cxpb=crossover_rate, mutpb=mutation_rate, ngen=n_generations,
                        stats=None, halloffame=None, verbose=True)

    best_individual = tools.selBest(population, k=1)[0]

    best_params = {}
    if model_type == 'rf':
        best_params = {
            'n_estimators': int(best_individual[0]),
            'max_depth': int(best_individual[1]),
            'min_samples_split': int(best_individual[2])
        }
    elif model_type == 'xgb':
        best_params = {
            'n_estimators': int(best_individual[0]),
            'max_depth': int(best_individual[1]),
            'learning_rate': best_individual[2]
        }
    elif model_type == 'mlp':
        best_params = {
            'hidden_layer_sizes': (int(best_individual[0]), int(best_individual[1]), int(best_individual[2])),
            'alpha': best_individual[3],
            'learning_rate_init': best_individual[4]
        }

    print(f"Optimized hyperparameters for {model_type}: {best_params}")
    return best_params

if __name__ == '__main__':
    model = Model(model_type='mlp')  # Adjust this to your desired model type
    print(genetic_hyperparameter_optimization(model.X, model.y, model.y_column, model_type=model.model_type))
