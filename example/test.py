import _
import math
from time import time
from experiments_utils.experiment import *
from test_config import *
import time

__version__ = '0.0.1'


@step('add')
def add(a: float, b: float, logger: logging.Logger, context: ExperimentContext) -> float:
    logger.info(f'Add a + b = { a + b} (a = {a}, b = {b})')
    return a + b


@step('multiply')
def multiply(a: float, b: float, logger: logging.Logger, context: ExperimentContext) -> float:
    if context.config_name == '4':
        print('wait')
        time.sleep(5000)
    logger.info(f'Multiply a + b = {a * b } (a = {a}, b = {b})')
    return a * b


@step('power')
def power(a: float, b: float, logger: logging.Logger, context: ExperimentContext) -> float:
    logger.info(f'Power a^b = {math.pow(a, b)} (a = {a}, b = {b})')
    return math.pow(a, 2)


@experiment('test', CONFIGURATIONS, __file__, version=__version__)
def experiment(a: int, b: int, logger: logging.Logger, context: ExperimentContext):
    config_name: str = context.config_name
    s = State(context)
    s.add_result = add(a, b, context=context)
    s.multiply_result = multiply(a, b, context=context)
    time.sleep(5)
    s.power_result = power(a, b, context=context)
    logger.info(f'Result is: {s.power_result}')
    with open(f'{settings.dir_path}/results/{context.config_name}', 'w+') as results_file:
        results_file.write(s.power_result)


if __name__ == '__main__':
    experiment()
