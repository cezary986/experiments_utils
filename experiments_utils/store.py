import os
from logging import getLogger
from typing import Any

import cloudpickle

from .context import ExperimentContext


class Store(object):
    """Special object for storing experiment internal state. Every attribute set to this
    object is automatically cached (pickled and stored to file). Each read attribute of this
    object is taken from cache (last stored value).

    Basic example:

    ```python
    from experiments_utils import Store

    s = Store()
    s.a = 1
    print(s.a) # 1
    ```

    Typed Store example (preferable):

    ```python
    from experiments_utils import Store

    class MyStore(Store):
        model: MyModelClass
        training_time: float
        ...

    s = MyStore()
    s.model, s.training_time = train_my_mode()
    print(s.training_time) # 1
    ```
    """

    def __init__(self) -> None:
        """Constructor can only be used inside experiment or step functions.
        If you want to use Store outside experiment or step - use store_factory()
        function
        """
        context: ExperimentContext = ExperimentContext.__GLOBAL_CONTEXT__
        object.__setattr__(self, "__variables__", {})
        params_file_path = (
            f"{context.current_dir}/_cache/{context.version}/{context.paramset_name}"
        )
        object.__setattr__(self, "__params_base_dir_path", params_file_path)

    def __getattribute__(self, name: str) -> Any:
        if name == "__variables__":
            return object.__getattribute__(self, "__variables__")
        if name == "_Store__retrieve_variable":
            return object.__getattribute__(self, "_Store__retrieve_variable")
        if name == "_Store__save_variable":
            return object.__getattribute__(self, "_Store__save_variable")
        if name == "__class__":
            return Store
        if name == "__module__":
            return __file__
        if name == "__dict__":
            return {}
        else:
            return self.__retrieve_variable(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self.__save_variable(name, value)
        # store in memory
        self.__variables__[name] = value

    def __save_variable(self, name: str, value: Any):
        os.makedirs(
            object.__getattribute__(self, "__params_base_dir_path"), exist_ok=True
        )
        path = (
            f'{object.__getattribute__(self, "__params_base_dir_path")}/{name}.pickle'
        )
        with open(path, "wb+") as params_file:
            cloudpickle.dump(value, params_file)

    def __retrieve_variable(self, name: str) -> Any:
        # try to retrieve from memory
        if name in self.__variables__:
            return self.__variables__[name]
        var_file_path = (
            f'{object.__getattribute__(self, "__params_base_dir_path")}/{name}.pickle'
        )
        if os.path.exists(var_file_path):
            with open(var_file_path, "rb") as var_file:
                value = cloudpickle.load(var_file)
                # store in memory
                self.__variables__[name] = value
                return value
        else:
            raise NameError(f"name '{name}' is not defined")


class _ReadOnlyStore(Store):

    def __setattr__(self, name: str, value: Any) -> None:
        raise Exception("Store is read-only")


def store_factory(
    experiment_name: str,
    version: str,
    paramset_name: str,
    current_dir: str,
    read_only: bool = True,
) -> Store:
    """Creates store object for given experiment version and paramset. This function
    can only be used outside experiment or step functions for accessing or modyfing
    store. By default it will return read-only instance of store to prevent unwanted
    modifications. If `read_only` is set to False, it will return writeable store.

    Args:
        experiment_name (str): name of experiment
        version (str): version of experiment
        paramset_name (str): name of paramset
        current_dir (str): current working directory of the experiment
        read_only (bool, optional): controls if store is read-only. Defaults to True.

    Raises:
        Exception: _description_

    Returns:
        Store: _description_
    """
    context = ExperimentContext(
        name=experiment_name,
        paramsets_names=[paramset_name],
        paramset_name=paramset_name,
        current_dir=current_dir,
        version=version,
        logger=getLogger(),
        logs_dir=None,
        plugins={},
    )

    if ExperimentContext.__GLOBAL_CONTEXT__ is not None:
        raise Exception(
            "This function cannot only be used inside experiment or step functions. "
            "Use Store constructor directly instead. Example: `store = Store()`"
        )
    ExperimentContext.__GLOBAL_CONTEXT__ = context
    store: Store = _ReadOnlyStore() if read_only else Store()
    ExperimentContext.__GLOBAL_CONTEXT__ = None

    if not os.path.exists(object.__getattribute__(store, "__params_base_dir_path")):
        raise Exception("No store exists for given experiment, version and paramset.")
    return store
