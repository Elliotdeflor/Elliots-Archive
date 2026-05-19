import pandas as pd
def create_data_structure(name, columns, data_types): #str, array, array

    return df

def get_data_structure(name): #str
    data_structures = pd.read_csv(r'..\meta\data-structures.csv')
    data_structure = data_structures
    print(list(data_structure))

def delete_data_structure(name):
    pass

def list_data_structures():
    pass

def get_data_types():
    data_types = ['str', 'int', 'float', 'bool']
    return data_types

def get_columns():
    columns = ['composition', 'phase', 'hardness', 'yield_strength', 'young_modulus']
    return columns

def init_data_types_csv():
    data_structures = pd.DataFrame(columns=['name','columns','datatypes'])
    columns = get_columns()
    data_types = get_data_types()
    data_structures.loc[0] = ("core-data", columns, data_types)
    data_structures.to_csv(r'..\meta\data-structures.csv')

def get_core_data():

if __name__ == '__main__':
    init_data_types_csv()
    df = get_data_structure('core-data')

