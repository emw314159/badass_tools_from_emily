
#
# load useful libraries
#
import pprint as pp
import pandas as pd

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from numpy import percentile
import sys
import random
import json
import pickle

import badass_tools_from_emily.machine_learning.machine_learning as ml
import badass_tools_from_emily.machine_learning.random_forest as rf

#
# load configuration
#
with open(sys.argv[1]) as f:
    config = json.load(f)


#
# user settings
#
random.seed(config['seed'])
output_directory = config['output_directory']
bad_cutoff_percentile = config['bad_cutoff_percentile']
good_cutoff_percentile = config['good_cutoff_percentile']
number_of_vfolds_to_run = config['number_of_vfolds_to_run']
cost = config['cost']
gamma = config['gamma']
lead_variable = config['lead_variable']
formula = config['formula']
factor_options = config['factor_options']
libsvm_root = config['libsvm_root']
full_model_file = config['full_model_file']

#
# load data
#
df = pd.read_csv(output_directory + '/data_for_model.csv')
df = df.sample(frac=0.05)
#df = df.sample(frac=0.001)
print len(df.index)

#
# decide on percentiles
#
print
print len(df.index)
print percentile(df[lead_variable], [bad_cutoff_percentile, good_cutoff_percentile])
bad_cutoff = percentile(df[lead_variable], bad_cutoff_percentile)
good_cutoff = percentile(df[lead_variable], good_cutoff_percentile)
print


#
# apply cutoffs
#
df_to_use = df.ix[(df[lead_variable] <= bad_cutoff) | (df[lead_variable] >= good_cutoff), :].copy()
y = []
for x in df_to_use[lead_variable]:
    if x <= bad_cutoff:
        y.append(0.)
    elif x >= good_cutoff:
        y.append(1.)
    else:
        print
        print 'Something went wrong.'
        print
        sys.exit(0)
df_to_use['y'] = y


#
# set up model
#
y, X = ml.categorize(formula, factor_options, df_to_use, add_intercept=False)

model = ml.random_forest_classification_wrapper(y, X, n_jobs=100)

feature_importances = model.model.feature_importances_

fi_dict = {}
for h, fi in zip(list(X.columns.values), feature_importances):
    fi_dict[h] = fi

rf.plot_feature_importances(fi_dict, 'Relative Feature Importances', output_directory + '/feature_importances.png')











