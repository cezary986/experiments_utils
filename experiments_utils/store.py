import pickle
import os
from typing import Any
from .context import ExperimentContext


class Store(object):
    """Special object for storing experiment internal state. Every attribute set to this
    object is automatically cached (pickled and stored to file). Each readed attribute of this
    object is taken from cache (last stored value). 
    """

    def __init__(self) -> None:
        context: ExperimentContext = ExperimentContext.__GLOBAL_CONTEXT__
        object.__setattr__(self, '__variables__', {})
        params_file_path = f'{context.current_dir}/_cache/{context.version}/{context.paramset_name}'
        object.__setattr__(self, '__params_base_dir_path', params_file_path)

    def __getattribute__(self, name: str) -> Any:
        if name == '__variables__':
            return object.__getattribute__(self, '__variables__')
        if name == '_Store__retrieve_variable':
            return object.__getattribute__(self, '_Store__retrieve_variable')
        if name == '_Store__save_variable':
            return object.__getattribute__(self, '_Store__save_variable')
        if name == '__class__':
            return Store
        if name == '__module__':
            return __file__
        if name == '__dict__':
            return {}
        else:
            return self.__retrieve_variable(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self.__save_variable(name, value)

    def __save_variable(self, name: str, value: Any):
        os.makedirs(object.__getattribute__(
            self, '__params_base_dir_path'), exist_ok=True)
        path = f'{object.__getattribute__(self, "__params_base_dir_path")}/{name}.pickle'
        with open(path, 'wb+') as params_file:
            pickle.dump(value, params_file)

    def __retrieve_variable(self, name: str) -> Any:
        var_file_path = f'{object.__getattribute__(self, "__params_base_dir_path")}/{name}.pickle'
        if os.path.exists(var_file_path):
            with open(var_file_path, 'rb') as var_file:
                return pickle.load(var_file)
        else:
            raise NameError(f"name '{name}' is not defined")
