import re
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from model_class import *
def get_all_not_null(df):
    non_null_rows = pd.DataFrame(columns=df.columns)
    non_null_rows = df.dropna(how='any')
    return non_null_rows


import re
import numpy as np
import pandas as pd
import swifter
from sklearn.model_selection import train_test_split
from model_class import *


def split_composition(composition):
    """Extract elements and their amounts from composition string using regex."""
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition)
    return {element.lower(): float(amount) if amount else 1.0 for element, amount in matches}


def composition_to_percentages(composition_dict):
    """Convert element amounts to percentage fractions."""
    total = sum(composition_dict.values())
    return {key: val / total for key, val in composition_dict.items()}


def get_phases():
    return ['BCC', 'FCC', 'Other']


def get_phase_array(phase):
    """Return a one-hot encoded array for phase classification."""
    phases = get_phases()
    phase_array = np.zeros(len(phases))
    phase_array[phases.index(phase) if phase in phases else -1] = 1
    return phase_array


def get_elements():
    return sorted(['Co', 'Fe', 'Ni', 'Si', 'Al', 'Ti', 'Cr', 'Mo', 'Nb', 'C', 'Mn', 'Cu', 'V', 'Y', 'Zr', 'B',
                   'Mg', 'Sn', 'Zn', 'Sc', 'Li', 'Ta', 'Hf', 'W'])


elements = get_elements()  # Cache element list


def get_element_array(composition):
    """Efficiently convert composition string to element array using vectorized mapping."""
    composition_dict = composition_to_percentages(split_composition(composition))
    return np.array([composition_dict.get(el.lower(), 0) for el in elements])


def create_training_dataframe_struc(cols):
    """Initialize an empty DataFrame with required columns."""
    structure = get_elements() if 'composition' in cols else []
    structure += [col for col in cols if col not in ['composition', 'phase']]
    structure += get_phases() if 'phase' in cols else []
    return pd.DataFrame(columns=structure)


def process_row(row, columns):
    """Optimized row processing function."""
    row_data = []
    for col in columns:
        if col == 'composition':
            row_data.extend(get_element_array(row[col]))
        elif col == 'phase':
            row_data.extend(get_phase_array(row[col]))
        else:
            row_data.append(row[col])
    return row_data


def create_training_dataframe(file_df, columns):
    """Optimized training DataFrame creation with parallel processing."""
    if 'composition' in columns:
        elements = get_elements()
    else:
        elements = []
    if 'phase' in columns:
        phases = get_phases()
    else:
        phases = []
    processed_data = file_df[columns].swifter.apply(lambda row: process_row(row, columns), axis=1).tolist()
    columns = elements + [col for col in columns if col not in ['composition', 'phase']] + phases
    return pd.DataFrame(processed_data, columns=columns)


def get_train_test_split(df, x_columns_input, y_column, test_size=0.5, random_state='random'):
    import random
    random_state= random.randint(0,400000)
    print("random state:", random_state)
    """Efficiently split dataset into training and test sets."""
    y_name = get_elements() if y_column == 'composition' else get_phases() if y_column == 'phase' else y_column
    x_columns = sum([get_elements() if col == 'composition' else get_phases() if col == 'phase' else [col] for col in
                     x_columns_input], [])
    y = encode_phase(df[y_name]) if y_column == 'phase' else df[y_name]
    return train_test_split(df[x_columns].values, y.values, test_size=test_size, random_state=random_state)


import numpy as np


def encode_phase(df):
    """Converts one-hot encoded phase columns (BCC, FCC, Other) into a single categorical column 'phase'."""
    phase_columns = ["BCC", "FCC", "Other"]

    # Ensure phase columns exist
    if not all(col in df.columns for col in phase_columns):
        raise ValueError(f"Missing phase columns! Expected {phase_columns}, found {df.columns.tolist()}")

    # Find index of max value (0 for BCC, 1 for FCC, 2 for Other)
    phase_values = np.argmax(df[phase_columns].values, axis=1)

    # If all are zero, set to 3
    phase_values[np.all(df[phase_columns].values == 0, axis=1)] = 3

    # Assign to new column and drop old one-hot columns
    df["phase"] = phase_values
    df = df.drop(columns=phase_columns)

    return df


def get_core_data():
    """Efficiently load and filter core dataset."""
    df = pd.read_csv('../mat-data.csv',
                     usecols=['composition', 'phase', 'density', 'hv', 'yield_strength', 'young_modulus'])
    return df.dropna()


def get_x_and_y(df, x_columns_input, y_column, fill=False):
    """Extract and preprocess features & labels efficiently."""
    if not fill:
        df = df.dropna()

    y_name = get_elements() if y_column == 'composition' else get_phases() if y_column == 'phase' else y_column
    x_columns = sum([get_elements() if col == 'composition' else get_phases() if col == 'phase' else [col] for col in
                     x_columns_input], [])

    y = encode_phase(df[y_name]) if y_column == 'phase' else df[y_name]
    return df[x_columns].values, y.values


def concatenate_dataframes(df_list, axis=0, ignore_index=False):
    """Efficient DataFrame concatenation."""
    return pd.concat(df_list, axis=axis, ignore_index=ignore_index)


if __name__ == '__main__':
    size = len(['d','h','y','y',])+5 + len(get_elements())
    print(size)