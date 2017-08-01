
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
# user settings
#
random.seed(234)
output_directory = 'output'
plot_directory = '/Users/emily/Desktop/stocks'
bad_cutoff_percentile = 40.
good_cutoff_percentile = 85.
number_of_vfolds_to_run = 100
number_of_random_forest_jobs = 2000
lead_variable = 'percent_diff_lead_1_to_lead_2'
file_to_load = 'output/TEMP_data_for_modeling.csv'
compute_rf = True

#formula = 'y ~ lag_0 + lag_1 + lag_2 + lag_3 + lag_4 + lag_5 + len_features_list + mean_median_diff + p_0 + p_100 + p_25 + p_50 + p_75 + percent_high_month + percent_high_quarter + percent_high_year + C(weekday)'

formula = 'y ~ lag_0 + lag_1 + lag_2 + lag_3 + lag_4 + lag_5 + p_50 + percent_high_month + p_0 + p_100 + len_features_list + mean_median_diff + percent_high_year'




factor_options = {
    'weekday' : ['M', 'Tu', 'W', 'Th', 'F']
    }

#
# load data
#
df = pd.read_csv(file_to_load)

#
# get rid of any NaNs
#
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
print percentile(df[lead_variable], [bad_cutoff_percentile, good_cutoff_percentile])
bad_cutoff = percentile(df[lead_variable], bad_cutoff_percentile)
good_cutoff = percentile(df[lead_variable], good_cutoff_percentile)
print

#
# apply cutoffs given computed percentiles
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
# figure out which features matter the most using random forest classification
#
if compute_rf:
    yrf, Xrf = ml.categorize(formula, factor_options, df_to_use, add_intercept=False)
    model = ml.random_forest_classification_wrapper(yrf, Xrf, n_jobs=number_of_random_forest_jobs)
    feature_importances = model.model.feature_importances_
    fi_dict = {}
    for h, fi in zip(list(Xrf.columns.values), feature_importances):
        fi_dict[h] = fi
    rf.plot_feature_importances(fi_dict, 'Relative Feature Importances', plot_directory + '/feature_importances.png')

#
# get full model for logistic regression
#
model = ml.logit_wrapper(y, X)
with open(output_directory + '/logit_model.pickle', 'w') as f:
    pickle.dump(model, f)

#
# cross-validate
#
results = ml.v_fold(ml.logit_wrapper, y, X, number_of_vfolds_to_run)

print
pp.pprint(results['auc_list'])
print

#
# plot histogram and ROC plots for the cross-validation effort
#
ml.plot_auc_histogram(results, 'Cross-Validation AUC Histogram (n = ' + str(number_of_vfolds_to_run) + ')', plot_directory + '/HIST_AUC.png', color='lightblue')

fpr, tpr, roc_auc, thresholds = ml.plot_a_representative_ROC_plot(results, 'ROC Curve for Stock Prediction', plot_directory + '/ROC.png')

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



