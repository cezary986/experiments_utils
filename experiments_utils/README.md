# Experiments utils

Microframework to speed up writing scientific experiment code.

It aims at solving the most popular problems so you can focus on writing your experiment logic.
Some features that come out of the box are:
* fine-grained logging
* caching and rerunning only certain parts of an experiment
* parallel execution using multiprocessing

## Experiment

Imagine you came up with a great idea for a Machine Learning model and you want to try it out and see how good it is and how it compares to other popular models. You begin by writing a simple code for an experiment. It may look somehow like this:

```python

def main():
    df = pd.read_csv('./datasets/iris.csv')
    y = df['class']
    X = df.drop('class', 1)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.33)
    
    model = MyModel()
    model.fit(X_train, X_test)

    evaluate_model(model, './my_model_results.csv')

    model = XGBClassifier()
    model.fit(X_train, X_test)

    evaluate_model(model, './xgboost_results.csv')


if __name__ == '__main__':
    main()

```

You run it, and get results. Everything is nice but you know such results given only one dataset and one model for comparison is not enough. You need to add more datasets and more models to compare to. It will likely make your experiment run much longer. Depending on datasets it may take hours or days to complete. Running each dataset and model one by one is likely not optimal and some parallelization could improve execution time. Also, you need to remember about error handling so that even if a certain model or dataset will fail you won't lose everything and won't need to rerun from scratch. Also, some logs for possible errors will be useful to know which part of the experiment should be rerun. 

Quite a lot of things isn't it? And your nice short and simple code becomes not so simple and not so short. You end up spending time writing errors handling, logging, and parallelization code instead of focusing on what you want to research.

How this example would look like using `experiments_utils`?

```python
from experiments_utils import experiment
from glob import glob
import os


MODELS_TO_TRY = [
    MyModel(),
    XGBClassifier(),
    DecisionTreeClassifier(),
    ...
]

PARAMSETS = {}

for path in glob('./datasets/'):
    dataset_name = os.path.basename(path)
    for model in MODELS_TO_TRY:
        model_name = model.__class__.__name__
        PARAMSETS[f'{dataset_name}.{model_name}'] = {
            'dataset_name': dataset_name,
            'model_name': model_name,
            'model': model,
        }


@experiment(
    name='My Experiment',
    version='1.0.0',
    paramsets=PARAMSETS,
)
def main(
    dataset_name: str,
    model_name: str,
    model,
):
    df = pd.read_csv(f'./datasets/{dataset_name}.csv')
    y = df['class']
    X = df.drop('class', 1)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.33)
    
    model.fit(X_train, X_test)
    evaluate_model(model, f'./{model_name}__on__{dataset_name}.csv')


if __name__ == '__main__':
    main()
```

What has changed? 
* Experiment function was decorated by `experiment` decorator, given name and version (used for logging).
* `PARAMSETS` dictionary was generated containing sets of parameters for which your experiment function will run. Keys in this dictionary are used for logging. 

And that's it! Now you can call the `main` function with no params (they will be taken from the `PARAMSETS` dictionary). This will run your function for all given sets of parameters in parallel using multiprocessing. It will automatically produce default logs with execution time and information about certain paramset start and end and possible errors. Not if any of your paramset produce an error you don't need to rerun everything.

But we can do better than this...

Imagine that everything was great but you find some nasty bug in your `MyModel` predict method. It does not affect training performance but your evaluation results of `MyModel` are all wrong. With the code, you have all you can do is rerun the whole training and testing for all datasets for your model. Wouldn't it be nice if you could just run the evaluation part without having to train the model again? We can of course serialize (pickle) model after being trained and later load to skip the training phase but writing this yourself again adds some boilerplate. For such occasions `Store` class exists. Using it we can rewrite our code to something like this:

```python
...
from experiments_utils import experiment, Store

...

@experiment(
    name='My Experiment',
    version='1.0.0',
    paramsets=PARAMSETS,
)
def main(
    dataset_name: str,
    model_name: str,
    model,
):
    s = Store()
    df = pd.read_csv(f'./datasets/{dataset_name}.csv')
    y = df['class']
    X = df.drop('class', 1)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)
    
    model.fit(X_train, X_test)
    s.model = model
    evaluate_model(s.model, f'./{model_name}__on__{dataset_name}.csv')

...
```

As you can see `Store` object that created and trained the model was assigned to one of its fields. This object works slightly similar to a dictionary. You can put there something and receive it. Assigning to its fields creates a pickle file underhood where the value of this field is stored. All pickles are stored in a special `_cache` directory.

Given this behavior, we can now comment out certain lines of the code and run only those we want to. For example:

```python
...

...

@experiment(
    name='My Experiment',
    version='1.0.0',
    paramsets=PARAMSETS,
)
def main(
    dataset_name: str,
    model_name: str,
    model,
):
    s = Store()
    df = pd.read_csv(f'./datasets/{dataset_name}.csv')
    y = df['class']
    X = df.drop('class', 1)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33)
    
    # model.fit(X_train, X_test)
    # s.model = model
    evaluate_model(s.model, f'./{model_name}__on__{dataset_name}.csv')

...
```

Now model training is skipped and the model instance is taken from the `Store` object by reading it from the pickle file from the last known value. Now you can repeat only a minimal amount of code you need. This can save you a lot of time.


