import os
from glob import glob
from typing import List
import pandas as pd
from experiments_utils.datsets_helpers import sort_dataset_by_complexity
dir_path = os.path.dirname(os.path.realpath(__file__))


def retrieve_dataset(name: str) -> pd.DataFrame:
    return pd.read_csv(f'{dir_path}/datasets/{name}/original/{name}.csv')


datasets_names: List[str] = list(
    map(lambda path: os.path.basename(path), glob(f'{dir_path}/datasets/*')))

sorted_datasets = sort_dataset_by_complexity(
    datasets_names, dataset_accessor=retrieve_dataset)
sorted_datasets = list(map(lambda e: e['name'], sorted_datasets))
import json
print(json.dumps(sorted_datasets, indent=2))
