import sys
sys.path.append('..')

import numpy as np
import pandas as pd
import torch

from tools.cluster_analysis import *
from tools.neural_dataset import *
from tools.evaluation_metrics import *
from tools.evaluate_caterpillar import *


feature_columns = ['estar', 'jrstar', 'jzstar', 'jphistar', 'rstar', 'vstar', 'vxstar', 'vystar', 'vzstar', 'vrstar', 'vphistar', 'phistar', 'zstar']

def filterer(df):
    return df.loc[df['redshiftstar']<2].copy()

dataset = PointDataset(feature_columns, 'cluster_id',)

def evaluate_param(min_cluster_size, min_samples):
    clusterer = C_HDBSCAN(metric='euclidean', min_cluster_size=min_cluster_size, min_samples=min_samples, cluster_selection_method='eom')
    evaluator = CaterpillarEvaluator(clusterer, dataset, 1000000, filterer=filterer, run_on_test=True)
    f_metrics = evaluator.evaluate_all()
    return f_metrics

results = {}
for min_cluster_size in [2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,20,24,30,40,55,70]:
    metric = evaluate_param(min_cluster_size, None)
    results[min_cluster_size] = metric


with open('../results/hdbscan_caterpillar.json', 'w') as f:
    json.dump(results, f)