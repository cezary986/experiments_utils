from typing import Callable, List, Union
import pandas as pd
import numpy as np


def calculate_df_complexity(dataset: Union[np.ndarray, pd.DataFrame]) -> int:
    return dataset.shape[0] * (dataset.shape[1] * dataset.shape[1])


def sort_dataset_by_complexity(
    datasets: List[str],
    dataset_accessor: Callable[[str], Union[pd.DataFrame, np.ndarray]]
) -> List[str]:
    sorted_datasets: List[dict] = []
    for dataset_name in datasets:
        dataset: Union[pd.DataFrame, np.ndarray] = dataset_accessor(dataset_name)
        dataset_complexity: int = calculate_df_complexity(dataset)
        sorted_datasets.append({'name': dataset_name, 'complexity': dataset_complexity})
    return sorted(sorted_datasets, key=lambda e: e['complexity'])    
