
#
# load useful libraries
#
import pprint as pp
import pandas as pd
import matplotlib.pyplot as plt
from numpy import percentile
import sys
import random

import badass_tools_from_emily.machine_learning.machine_learning as ml

#
# user settings
#
random.seed(23423)
output_directory = 'output'
bad_cutoff_percentile = 50.
good_cutoff_percentile = 80.
number_of_vfolds_to_run = 10
lead_variable = 'close_lead_2'

drop = ['close', 'volume_symbol', 'date', 'close_sector', 'volume_sector', 'close_industry', 'volume_industry',
        'same_industry', 'same_sector']

formula = 'y ~ close_lag_0 + close_lag_1 + close_lag_2 + close_lag_3 + close_lag_4 + close_lag_5 + close_percent_12_week_high + close_percent_4_week_high + close_percent_52_week_high + close_percent_diff_volume + p_log_10 + same_industry + same_sector + volume_lag_0 + volume_lag_1 + volume_lag_2 + volume_lag_3 + volume_lag_4 + volume_lag_5 + volume_percent_12_week_high + volume_percent_4_week_high + volume_percent_52_week_high + volume_percent_diff_volume + C(weekday)'

factor_options = {
    'weekday' : ['M', 'Tu', 'W', 'Th', 'F'],
    }

#
# load data
#
df = pd.read_csv(output_directory + '/data_for_model.csv')
for d in drop:
    del(df[d])

#
# plot distribution of close_lead_2
#
plt.figure()
plt.hist(df[lead_variable])
plt.savefig(output_directory + '/HIST_close_lead_2.png')
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
# cross-validate
#
results = ml.v_fold(ml.logit_wrapper, y, X, number_of_vfolds_to_run)
fpr, tpr, roc_auc = ml.plot_a_representative_ROC_plot(results, 'ROC Curve for Stock Prediction', output_directory + '/ROC.png')

#
# figure out where 80% TPR is
#
for i, r in enumerate(tpr):
    if r >= 0.8:
        break
print
print 'False positive rate at 80% true positive rate: ' + str(fpr[i])
print









