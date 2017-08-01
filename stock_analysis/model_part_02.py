
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
bad_cutoff_percentile = 40. #config['bad_cutoff_percentile']
good_cutoff_percentile = 95. #config['good_cutoff_percentile']
number_of_vfolds_to_run = 5 # config['number_of_vfolds_to_run']
cost = 2.**5. #config['cost']
gamma = 2.**-7. #config['gamma']
lead_variable = config['lead_variable']
formula = config['formula']
factor_options = config['factor_options']
libsvm_root = config['libsvm_root']
full_model_file = config['full_model_file']

#
# load data
#
df = pd.read_csv(output_directory + '/data_for_model.csv')
#df = df.sample(frac=0.05)
#print len(df.index)


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
model = ml.svm_wrapper(y, X, c=cost, g=gamma, output_file=full_model_file, libsvm_root=libsvm_root)
with open(full_model_file + '.pickle', 'w') as f:
    pickle.dump(model, f)

sys.exit(0)

#python ~/packages/libsvm-3.22/tools/grid.py -svmtrain ~/packages/libsvm-3.22/svm-train -gnuplot /usr/bin/gnuplot -png output/grid.png -out output/grid.out -b 1 output/FULL_SVM.scaled



#
# cross-validate
#
results = ml.v_fold(ml.svm_wrapper, y, X, number_of_vfolds_to_run, c=cost, g=gamma, output_file='output/SVM_CV', libsvm_root=libsvm_root)


ml.plot_auc_histogram(results, 'Cross-Validation AUC Histogram', output_directory + '/HIST_AUC.png')



fpr, tpr, roc_auc, thresholds = ml.plot_a_representative_ROC_plot(results, 'ROC Curve for Stock Prediction', output_directory + '/ROC.png')
print
pp.pprint(results['auc_list'])
print

#
# save fpr, tpr, roc_auc, thresholds
#
to_save = {
    'fpr' : fpr,
    'tpr' : tpr,
    'roc_auc' : roc_auc,
    'thresholds' : thresholds,
}
with open(output_directory + '/fpr_tpr_thresholds.pickle', 'w') as f:
    pickle.dump(to_save, f)


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










