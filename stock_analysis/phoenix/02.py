import sys
sys.path.insert(0, '/home/ec2-user')



#
# load useful standard libraries
#
import pprint as pp
import pandas as pd
from numpy import percentile, isnan, NaN
import sys
import random
import json
import pickle

#
# load my libraries
#
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
random.seed(config['random_seed'])
output_directory = config['output_directory']
plot_directory = config['images_directory']
buy_bad_cutoff_percentile = config['buy_bad_cutoff_percentile']
buy_good_cutoff_percentile = config['buy_good_cutoff_percentile']
number_of_vfolds_to_run = config['number_of_vfolds_to_run']
number_of_random_forest_jobs = config['number_of_random_forest_jobs']
file_to_load = config['data_for_modeling_file']
lead_variable = config['lead_variable']
full_model_file = config['buy_model_file']
libsvm_root = config['libsvm_root']
cost = config['cost']
gamma = config['gamma']
formula = config['formula']
factor_options = config['factor_options']
gnuplot_directory = config['gnuplot_directory']

compute_rf = True

#
# load data
#
print 'Loading data...'
df = pd.read_csv(file_to_load)

#
# get rid of any NaNs
#
print 'Getting rid of NaNs...'
idx_list = []
for i, idx in enumerate(df.index):
    fine = True
    for col in list(df.columns.values):

        if str(type(df[col][i])) != '<type \'str\'>':

            if isnan(df[col][i]):
                fine = False
                break

    if fine:
        idx_list.append(idx)

df = df.ix[idx_list,:].copy()

#
# decide on percentiles
#
print
print len(df.index)
print percentile(df[lead_variable], [buy_bad_cutoff_percentile, buy_good_cutoff_percentile])
buy_bad_cutoff = percentile(df[lead_variable], buy_bad_cutoff_percentile)
buy_good_cutoff = percentile(df[lead_variable], buy_good_cutoff_percentile)
print

#
# apply cutoffs given computed percentiles
#
df_to_use = df.ix[(df[lead_variable] <= buy_bad_cutoff) | (df[lead_variable] >= buy_good_cutoff), :].copy()
y = []
for x in df_to_use[lead_variable]:
    if x <= buy_bad_cutoff:
        y.append(0.)
    elif x >= buy_good_cutoff:
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

#
# figure out which features matter the most using random forest classification
#
if compute_rf:
    yrf, Xrf = ml.categorize(formula, factor_options, df_to_use, add_intercept=False)
    model = ml.random_forest_classification_wrapper(yrf, Xrf, n_jobs=number_of_random_forest_jobs)
    feature_importances = model.model.feature_importances_
    fi_dict = {}
    for h, fi in zip(list(Xrf.columns.values), feature_importances):
        fi_dict[h] = fi
    rf.plot_feature_importances(fi_dict, 'Relative Feature Importances', plot_directory + '/buy_feature_importances.png')


#
# get the full SVM model
#
model = ml.svm_wrapper(y, X, c=cost, g=gamma, output_file=full_model_file, libsvm_root=libsvm_root)
with open(full_model_file + '.pickle', 'w') as f:
    pickle.dump(model, f)

#
# cross-validate
#
results = ml.v_fold(ml.svm_wrapper, y, X, number_of_vfolds_to_run, c=cost, g=gamma, output_file='output/SVM_CV', libsvm_root=libsvm_root)



print
pp.pprint(results['auc_list'])
print

#
# plot histogram and ROC plots for the cross-validation effort
#
ml.plot_auc_histogram(results, 'Cross-Validation AUC Histogram (n = ' + str(number_of_vfolds_to_run) + ')', plot_directory + '/buy_HIST_AUC.png', color='lightblue')

fpr, tpr, roc_auc, thresholds = ml.plot_a_representative_ROC_plot(results, 'ROC Curve for Stock Prediction', plot_directory + '/buy_ROC.png')

#
# save fpr, tpr, roc_auc, thresholds
#
to_save = {
    'fpr' : fpr,
    'tpr' : tpr,
    'roc_auc' : roc_auc,
    'thresholds' : thresholds,
}
with open(full_model_file + '_fpr_tpr_thresholds.pickle', 'w') as f:
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

print 'python ' + libsvm_root + '/tools/grid.py -svmtrain ' + libsvm_root + '/svm-train -gnuplot ' + gnuplot_directory + ' -png ' + plot_directory + '/buy_grid.png -b 1 ' + full_model_file + '.scaled'
print

