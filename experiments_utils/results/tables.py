from __future__ import annotations

import logging
import os
import sys
from glob import glob
from typing import List

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


class Tables:

    _directory: str = None

    @staticmethod
    def configure(directory: str) -> Table:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        elif not os.path.isdir(directory):
            raise ValueError(f'Given path: "{directory}" is not a directory')
        elif len(os.listdir(directory)) != 0:
            logging.warn(f'Given tables directory: "{directory}" is not empty')
        Tables._directory = directory

    @staticmethod
    def get(*path) -> Table:
        path: List[str] = list(path)
        path[-1] = f"{path[-1]}.csv"
        table_file_path: str = os.path.join(Tables._directory, *path)
        return Table(table_file_path, False)

    @staticmethod
    def query(*path, as_pandas: pd.DataFrame = False) -> List[Table]:
        path: List[str] = list(path)
        path[-1] = f"{path[-1]}.csv"
        results_paths: List[str] = []
        pattern = os.path.join(Tables._directory, *path)
        results_paths += glob(pattern)
        res = [Table(path, False) for path in results_paths]
        if as_pandas:
            res = list(map(lambda table: table.as_pandas(), res))
        return res


class Table:

    def __init__(self, file_path: str, _called_explicilty: bool = True) -> None:
        if _called_explicilty:
            raise Exception(
                "Table class constructor should not be called exlicilty. "
                'You should obtain instance of Table via "Tables" class, '
                'using "get" or "query" method'
            )
        self._file_path: str = file_path
        self.name: str = os.path.basename(self._file_path).replace(".csv", "")
        self.rows: List[dict] = []
        # create empty placeholder file
        if not os.path.exists(self._file_path):
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            pd.DataFrame([]).to_csv(self._file_path, index=False)
        else:
            self._load()

    def _load(self):
        try:
            df: pd.DataFrame = pd.read_csv(self._file_path)
            self.rows = df.to_dict("records")
        except pd.errors.EmptyDataError:
            return pd.DataFrame([])

    def save(self):
        self.as_pandas().to_csv(self._file_path, index=False)

    def set_df(self, df: pd.DataFrame):
        self.rows = df.to_dict("records")
        self.save()

    def as_pandas(self) -> pd.DataFrame:
        df: pd.DataFrame = pd.DataFrame(self.rows)
        return df

    def as_numpy(self) -> np.ndarray:
        return self.as_pandas().to_numpy()


def concat_tables(tables: List[Table], result: Table):
    """Concatenate tables

    Args:
        tables (List[Table]): tables
        result (Table): result table for storing concatenated data
    """
    df: pd.DataFrame = pd.concat([table.as_pandas() for table in tables])
    result.set_df(df)


def mean_aggregate_tables(
    tables: List[Table], result: Table, cv_fold_column: str = None
):
    """Mean aggregate tables. For nominal columns, mode value is used as aggregated
    value

    Args:
        tables (List[Table]): tables
        result (Table): result table for storing aggregated data
        cv_fold_column (str, optional): optional name of the cv fold column to drop
            during aggregation. Defaults to None.
    """
    df: pd.DataFrame = pd.concat([table.as_pandas() for table in tables])
    result.set_df(df)

    df: pd.DataFrame = pd.concat([table.as_pandas() for table in tables])
    df = df.reset_index(drop=True)

    aggregate_dict = dict(
        [
            (
                (col, "mean")
                if is_numeric_dtype(df[col])
                else (col, lambda col: col.mode()[0])
            )
            for col in df.columns
        ]
    )
    if cv_fold_column:
        del aggregate_dict[cv_fold_column]
    df = pd.DataFrame(df.aggregate(aggregate_dict)).T.reset_index(drop=True)
    result.set_df(df)
