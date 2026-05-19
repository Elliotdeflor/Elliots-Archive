import numpy as np

from model_class import *


# periodic table csv found at
# https://github.com/sweaver2112/periodic-table-data-complete/blob/main/pTable.csv
def get_elements_properties():
    periodic_table_csv = pd.read_csv(r'..\meta\periodic_table.csv')
    periodic_table_filtered = periodic_table_csv[periodic_table_csv['symbol'].isin(dc.get_elements())]
    symbols = periodic_table_filtered['symbol']
    periodic_table_filtered.loc[:, 'symbol'] = pd.Categorical(symbols, categories=dc.get_elements())
    periodic_table_sorted = periodic_table_filtered.sort_values('symbol')
    return periodic_table_sorted


def get_atomic_size_difference(ml_df):
    pt = get_elements_properties()
    atomic_size_difference = []
    atomic_radii = pt['radius/empirical']
    composition_values = ml_df[(list(pt['symbol']))]
    for i in range(composition_values.shape[0]):
        mean = 0
        for j in range(len(atomic_radii)):
            composition = composition_values.iloc[i]
            mean += composition.iloc[j] * atomic_radii.iloc[j]
        diff = 0
        for j in range(len(atomic_radii)):
            diff += composition.iloc[j] * (1 - (atomic_radii.iloc[j] / mean))
        atomic_size_difference.append(diff)
    return atomic_size_difference


def get_atomic_mixing_entropy(ml_df):
    mixing_entropy_arr = []
    pt = get_elements_properties()
    composition_values = ml_df[(list(pt['symbol']))]
    R = 8.314  # universal gas constant
    for i in range(composition_values.shape[0]):
        composition = composition_values.iloc[i]
        mixing_entropy = 0
        for j in range(pt.shape[0]):
            if composition.iloc[j] > 0:
                mixing_entropy += composition.iloc[j] * np.log(composition.iloc[j])
        mixing_entropy = R * mixing_entropy
        mixing_entropy_arr.append(mixing_entropy)
    return mixing_entropy_arr


def get_electronegativity_difference(ml_df):
    pt = get_elements_properties()
    electronegativity_difference_arr = []
    electronegativity = pt['electronegativity_pauling']
    composition_values = ml_df[(list(pt['symbol']))]
    for i in range(composition_values.shape[0]):
        mean = 0
        for j in range(len(electronegativity)):
            composition = composition_values.iloc[i]
            mean += composition.iloc[j] * electronegativity.iloc[j]
        electronegativity_diff = 0
        for j in range(len(electronegativity)):
            if composition.iloc[j] > 0:
                electronegativity_diff += (composition.iloc[j] * (electronegativity.iloc[j] - mean) ** 2) ** 0.5
        electronegativity_difference_arr.append(electronegativity_diff)
    return electronegativity_difference_arr


def get_valence_electron_concentration(ml_df):
    pt = get_elements_properties()
    VEC_arr = []
    valence_electrons = pt['valence_electrons']
    composition_values = ml_df[(list(pt['symbol']))]
    for i in range(composition_values.shape[0]):
        VEC = 0
        for j in range(len(valence_electrons)):
            composition = composition_values.iloc[i]
            VEC += composition.iloc[j] * valence_electrons.iloc[j]
        VEC_arr.append(VEC)
    return VEC_arr


def add_thermodynamic_properties(ml_df):
    ml_df['VEC'] = get_valence_electron_concentration(ml_df)
    ml_df['atomic_mixing_entropy'] = get_atomic_mixing_entropy(ml_df)
    ml_df['atomic_size_difference'] = get_atomic_size_difference(ml_df)
    ml_df['electronegativity_difference'] = get_electronegativity_difference(ml_df)
    return ml_df


if __name__ == '__main__':
    elements = dc.get_elements()
    pt = get_elements_properties()
    model_class = Model(['composition', 'hv'], 'phase', model_type='rf')
    df = model_class.ml_df
    df = add_thermodynamic_properties(df)
    print(df.head())
