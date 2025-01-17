"""Contains helper utilities for cross validation
"""
from typing import Generic, TypeVar, Union

T = TypeVar('T')


class CvMixin(Generic[T]):
    """Mixing class simplifying storage of all kind of cross validation concerned data.
    This class behaves like a list allowing to access folds data by index.

    Example:
    ```python
    from experiments_utils.helpers.cv import CvMixin

    N_FOLDS: int = 10

    class CvModels(CvMixin[MyClass]):
        pass

    # building class instance
    cv_models = CvModels([MyClass(...) for _ in range(N_FOLDS)])

    # accessing items like in a list
    cv_models[0]
    cv_models[1:3]
    cv_models[-1]
    ...

    # accessing length
    len(cv_models) # 10
    ```
    """

    def __init__(self, folds_data: list[T]) -> None:
        if len(folds_data) == 0:
            raise ValueError('CV Mixin requires at least one fold')
        self._folds: list[T] = folds_data

    def __getitem__(self, key: Union[int, slice]) -> Union[T, list[T]]:
        if not isinstance(key, (int, slice)):
            raise TypeError('key must be int')
        return self._folds[key]

    def __len__(self) -> int:
        return len(self._folds)

