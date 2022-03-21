# Experiments utils

Bundle of helpers tools for fast and easy ML experiments writing.

Features that comes out of box:
* fine grained logging
* caching and reruning only certain part of experiment
* execution parallelization using threads

## Experiment

Writing experiment is simply writing a function and decorating it with `experiment` decorator. Complicated experiments could be splitted for steps which are also functions decorated with `step` decorators. 

```python
import time
from experiment import experiment, step
import math
from logging import Logger
from experiments_utils.experiment import *
from test_config import *
__version__ = '0.0.1'

CONFIGURATIONS: Dict[str, dict] = {
    'first': {
        'a': 1,
        'b': 2,
    },
    'second': {
        'a': 2,
        'b': 2
    }
}

@step('add')
def add(a: float, b: float, logger: Logger) -> float:
    logger.info(f'Add a + b = { a + b} (a = {a}, b = {b})')
    return a + b

@step('multiply')
def multiply(a: float, b: float, logger: Logger) -> float:
    logger.info(f'Multiply a + b = {a * b } (a = {a}, b = {b})')
    return a * b

@step('power')
def power(a: float, b: float, logger: Logger) -> float:
    logger.info(f'Power a^b = {math.pow(a, b)} (a = {a}, b = {b})')
    return math.pow(a, b)


@experiment('test', CONFIGURATIONS, __file__, version=__version__)
def experiment(a: int, b: int, logger: logging.Logger, **context):
    s = State(**context)
    s.add_result = add(a, b, **context)
    s.multiply_result = multiply(a, b, **context)
    s.power_result = power(a, b, **context)
    logger.info(f'Result is: {s.power_result}')


if __name__ == '__main__':
    experiment()

```

> All experiment variables must be stored in state object. Without it you
> will loose ability to replay parts of your experiment

> Experiments are being run using `ThreadPoolExecutor`. Maximum number of threads is 8 by default but
> could be increased by `exepriment` decorator param `max_threads`.

Now lets say your experiment fails on step **multiply** but step **sum** finished successfully. You don't have to rerun whole experiment. You can now fix your code and rerun from exact step that failed before. To do this just comment-out **everything** you don't want to run and leave only part of code you want to replay. Just as simple!

```python
@experiment('foo', configurations, __file__)
def foo(a: int, b: int, c: int, **context):
    s = State(**context)
    time.sleep(1)
    # s.ab = add(a, b, **context)
    # s.abc = multiply(s.ab, c, **context)
    s.abcd = divide(s.abc, s.ab, **context)
    print(s.abcd)
    ...
```

Not step `multiply` will be runned with last saved input params. This can saves a lot of time!

## Logging

By default experiments support fine grained logging out of box. Exery experiment and step function has `logger`. You don't have to worry about passing it will be done automagicly.

Example directory sturcture for experiment with configurations:

```python
CONFIGURATIONS = {
    'iris': {...},
    'credit_a': {...},
    'hepatitis': {...},
}
```

and steps:

```python
@step('preprocess')
def preprocess(df, logger):
    ...

@step('train')
def preprocess(df, logger):
    ...

@step('test')
def preprocess(df, logger):
    ...
```

Will look like this:

```
|-logs
|   |- log.DEBUG.log
|   |- log.INFO.log
|   |- log.WARN.log
|   |- log.ERROR.log
|   |
|   |- iris
|   |   |- preprocess
|   |   |   |- preprocess.DEBUG.log
|   |   |   |- preprocess.INFO.log
|   |   |   |- preprocess.WARN.log
|   |   |   |- preprocess.ERROR.log
|   |   |- train
|   |   |   |- preprocess.DEBUG.log
|   |   |   |- preprocess.INFO.log
|   |   |   |- preprocess.WARN.log
|   |   |   |- preprocess.ERROR.log
|   |   |- test
|   |   |   |- preprocess.DEBUG.log
|   |   |   |- preprocess.INFO.log
|   |   |   |- preprocess.WARN.log
|   |   |   |- preprocess.ERROR.log
|   |- credit_a
|   |- hepatitis
```

Such structure allows fine grained logging. If you want to see all logs see _.DEBUG.log file. If you want to see only errors logs go to _.ERROR.log.

## Experiments Preparations

It is good to run experiment starting in order starting from simplest to most complex datasets. You can sort your datasets based on complexity using special helper function. Example bellow:

```python
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
```
