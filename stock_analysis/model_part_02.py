
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

import badass_tools_from_emily.machine_learning.machine_learning as ml


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

#for d in drop:
#    del(df[d])






#
# plot distribution of close_lead_2
#
plt.figure()
plt.hist(df[lead_variable])
plt.savefig(output_directory + '/HIST_' + lead_variable + '.png')
plt.close()

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
y, X = ml.categorize(formula, factor_options, df_to_use)



#
# get full model for grid.py
#
#model = ml.svm_wrapper(y, X, c=cost, g=gamma, output_file=full_model_file, libsvm_root=libsvm_root)
#import sys; sys.exit(0)


#python ~/packages/libsvm-3.22/tools/grid.py -svmtrain ~/packages/libsvm-3.22/svm-train -gnuplot "null" -b 1 output/FULL_SVM.scaled




#
# cross-validate
#
results = ml.v_fold(ml.svm_wrapper, y, X, number_of_vfolds_to_run, c=cost, g=gamma, output_file='output/SVM_CV', libsvm_root=libsvm_root)






fpr, tpr, roc_auc = ml.plot_a_representative_ROC_plot(results, 'ROC Curve for Stock Prediction', output_directory + '/ROC.png')
print
pp.pprint(results['auc_list'])
print

#
# figure out where 80% TPR is
#
for i, r in enumerate(tpr):
    if r >= 0.8:
        break
print
print 'False positive rate at 80% true positive rate: ' + str(fpr[i])
print 'AUC = ' + str(roc_auc)
print










