from typing import Union, Callable

import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
import pandas as pd

from imblearn.combine import SMOTEENN

from sklearn.base import BaseEstimator
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.utils._testing import ignore_warnings
from sklearn.exceptions import ConvergenceWarning


def balance_data(X: pd.DataFrame,
                 y: Union[pd.Series, np.ndarray],
                 seed: int
                ):
    """
    Performs SMOTE followed by Edited Nearest Neighbors to attempt to balance
    the dataset.

    https://storm.cis.fordham.edu/~gweiss/selected-papers/batista-study-balancing-training-data.pdf

    Parameters
    ----------
    X
        data features
    y
        labels
    seed
        random seed for reproducability
    """
    smote_enn = SMOTEENN(random_state=seed)
    X_resamp, X_test, y_resamp, y_test = train_test_split(X, y, test_size=0.1, stratify=y, random_state=seed)
    X_resamp, y_resamp = smote_enn.fit_resample(X, y)
    return X_resamp, X_test, y_resamp, y_test


def prepare_model(model_type: BaseEstimator,
                  model_args: dict
                 ):
    """
    Instantiates an object of the given model with the provided arguments

    Parameters
    ----------
    model_type
        sklearn model to be created
    model_args
        arguments for the model to be created with
    """
    if model_args:
        model = model_type(**model_args)
    else:
        model = model_type()
    return model

@ignore_warnings(category=ConvergenceWarning)
def train_eval(model: BaseEstimator,
               X_train: Union[pd.DataFrame, np.ndarray],
               X_test: Union[pd.DataFrame, np.ndarray],
               y_train: Union[pd.Series, np.ndarray],
               y_test: Union[pd.Series, np.ndarray],
               metric: Callable,
               kfolds: int=5,
               seed: int=0
              ):
    """
    Trains and evaluates a sklearn model

    Parameters
    ----------
    model
        sklearn model instance
    X_train
        features for the training data
    X_test
        features for the testing data
    y_train
        labels for the training data
    y_test
        labels for the testing data
    metric
        sklearn scoring function
    kfolds
        number of folds for cross-validation
    seed
        random seed for reproducability
    """
    skf = StratifiedKFold(n_splits=kfolds, random_state=seed, shuffle=True)
    for train_idx, test_idx in skf.split(X_train, y_train):
        X_train_, X_test_ = X_train[train_idx], X_train[test_idx]
        y_train_, y_test_ = y_train[train_idx], y_train[test_idx]
        model.fit(X_train_, y_train_)
        preds = model.predict(X_test_)
        try:
            score = metric(y_test_, preds.round(0).astype(int))
        except:
            print(y_test_[:10], preds[:10])
            metric(y_test_, preds)

    preds = model.predict(X_test)
    final_score = metric(y_test, preds.round(0).astype(int))

    return final_score


def single_experiment(X: Union[pd.DataFrame, np.ndarray],
                      y: Union[pd.Series, np.ndarray],
                      model_type: BaseEstimator,
                      metric: Callable,
                      seed: int,
                      model_args: dict
                     ):
    """
    Conducts a single experiment.

    Includes:
        - data resampling to correct for imbalance
        - splitting into train/test sets
        - model training
        - model evaluation

    Parameters
    ----------
    X
        data features
    y
        data labels
    model_type
        sklearn model to use
    metric
        sklearn scoring function
    seed
        seed for reproducability
    model_args
        arguments to be passed to the model at instantiation
    """
    X_resamp, X_test, y_resamp, y_test = balance_data(X, y, seed)
    model = prepare_model(model_type, model_args)
    score = train_eval(model, X_resamp, X_test, y_resamp, y_test, metric)

    return score


def show_experiment_results(scores: np.ndarray):
    """
    Displays:
        - bar chart of scores
        - distribution of scores
        - box plot of scores
        - summary statistics

    Parameters
    ----------
    scores
        array of floats representing model performance scores
    """
    #Scatter plot
    fig, ax1 = plt.subplots(figsize=(6, 3), ncols=1)
    ax1.set_title("Experiment Scores")
    ax1.set_xlabel("Experiment")
    ax1.set_ylabel("Score")
    plt.bar(np.arange(len(scores)), scores)
    plt.show()

    #Violin and Box Plot
    fig, (ax1, ax2) = plt.subplots(figsize=(6, 3), ncols=2, sharey=False)
    ax1.set_title("Score Distribution")
    ax2.set_title("Score Box Plot")
    sns.kdeplot(scores, ax=ax1)
    sns.boxplot(scores, ax=ax2)
    plt.show()

    #Summary statistics
    print("=== Statistics ===")
    print("Mean: ", round(scores.mean(),4))
    print("Median: ", round(np.median(scores),4))
    print("Standard Dev: ", round(scores.std(),4))
    print("Range: ", (round(scores.min(),4), round(scores.max(),4)))


def run_experiments(seeds: np.ndarray,
                    X: Union[pd.DataFrame, np.ndarray],
                    y: Union[pd.Series, np.ndarray],
                    model_type: BaseEstimator,
                    metric: Callable,
                    model_args: dict={},
                    verbose: bool=True,
                    viz: bool=True
                   ):
    """
    Runs seeds.shape[0] experiments using the provided data and model

    Parameters
    ----------
    seeds
        array of random seeds for reproducability and to assess
        generalizability
    X
        data features
    y
        data labels
    model_type
        sklearn model
    metric
        sklearn scoring function
    model_args
        arguments to pass to the model at instantiation
    verbose
        print experiment results
    viz
        plot visuals and summary stats
    """
    scores = []

    for i,seed in enumerate(seeds):
        if verbose:
            print(f"Running experiment {i+1}")
        score = single_experiment(X, y, model_type, metric,
                                  seed, model_args)
        scores.append(score)
        if verbose:
            print(f"Completed experiment. Score: {score}")

    scores = np.array(scores)

    if viz:
        show_experiment_results(scores)

    return scores
