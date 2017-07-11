

from patsy import dmatrices, dmatrix, DesignInfo
import random
import pandas as pd
import uuid

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


from sklearn.metrics import roc_curve, auc
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score

from scipy.stats import spearmanr
from badass_tools_from_emily.misc import sort_lists_by_rank_of_another_list



#
# negative binomial regression
#
class negative_binomial_wrapper(object):
    def __init__(self, y, X):
        import statsmodels.api as sm
        self.X_header = list(X.columns.values)
        self.y_header = list(y.columns.values)
        family = sm.families.NegativeBinomial()
        self.model = sm.GLM(y, X, family=family).fit()
    def predict(self, X):
        return self.model.predict(X) 


#
# linear regression
#
class linear_wrapper(object):
    def __init__(self, y, X):
        from statsmodels.api import OLS
        self.X_header = list(X.columns.values)
        self.y_header = list(y.columns.values)
        self.model = OLS(y, X).fit()
    def predict(self, X):
        return self.model.predict(X) 
        

#
# logistic regression
#
class logit_wrapper(object):
    def __init__(self, y, X):
        from statsmodels.discrete import discrete_model
        self.X_header = list(X.columns.values)
        self.y_header = list(y.columns.values)
        self.model = discrete_model.Logit(y, X).fit()
    def predict(self, X):
        return self.model.predict(X) 

#
# random forest regression
#
class random_forest_regression_wrapper(object):
    def __init__(self, y, X, n_jobs=100):
        from sklearn.ensemble import RandomForestRegressor
        self.X_header = list(X.columns.values)
        self.y_header = list(y.columns.values)
        max_features = len(X.columns)
        self.model = RandomForestRegressor(n_jobs=n_jobs, n_estimators=5000, max_features=max_features, min_samples_split=2)
        y_to_use = list(y.iloc[:,0])
        self.model.fit(X.as_matrix(), y_to_use)
    def predict(self, X):
        return self.model.predict(X.as_matrix())


#
# random forest classification
#
class random_forest_classification_wrapper(object):
    def __init__(self, y, X, n_jobs=100):
        from sklearn.ensemble import RandomForestClassifier
        self.X_header = list(X.columns.values)
        self.y_header = list(y.columns.values)
        max_features = len(X.columns)
        self.model = RandomForestClassifier(n_jobs=n_jobs, n_estimators=5000, max_features=max_features, min_samples_split=2)
        y_to_use = list(y.iloc[:,0])
        self.model.fit(X.as_matrix(), y_to_use)
    def predict(self, X):
        return self.model.predict_proba(X.as_matrix())[:,1] 





#
# Generic v-fold cross validation
#
def v_fold(function, y, X, number_of_v_fold_cycles, classification=True, verbose=False, **kwargs):

    if classification:
        auc_list = []
        fpr_list = []
        tpr_list = []
        average_precision_list = []
        precision_list = []
        recall_list = []
    else:
        spearmanr_list = []
        y_testing_list = []
        y_predicted_list = []

    for n in range(0, number_of_v_fold_cycles):

        if verbose:
            print 'Iteration ' + str(n)

        yn = len(y)
        training_idx = random.sample( range(0, yn) , int(round(4. * float(yn) / 5.))) 
        training_idx_dict = {}
        for t in training_idx:
            training_idx_dict[t] = None
        training_idx = sorted(training_idx_dict.keys())
        testing_idx = [x for x in range(0, yn) if not training_idx_dict.has_key(x)]

        y_training = y.iloc[training_idx].copy()
        X_training = X.iloc[training_idx, :].copy()
        y_testing = y.iloc[testing_idx].copy()
        X_testing = X.iloc[testing_idx, :].copy()

        model = function(y_training, X_training, **kwargs)
        y_predicted = model.predict(X_testing)

        if classification:
            fpr, tpr, _ = roc_curve(y_testing, y_predicted)
            roc_auc = auc(fpr, tpr)
            average_precision = average_precision_score(y_testing, y_predicted)
            precision, recall, _ = precision_recall_curve(y_testing, y_predicted)
            fpr_list.append(list(fpr))
            tpr_list.append(list(tpr)) 
            auc_list.append(roc_auc)
            average_precision_list.append(average_precision)
            precision_list.append(list(precision))
            recall_list.append(list(recall))
        else:
            spearmanr_list.append(spearmanr(y_testing, y_predicted))
            y_testing_list.append(list(y_testing['y']))
            y_predicted_list.append(list(y_predicted))

    data_to_return = {}
    if classification:
        data_to_return['auc_list'] = auc_list
        data_to_return['fpr_list'] = fpr_list
        data_to_return['tpr_list'] = tpr_list
        data_to_return['average_precision_list'] = average_precision_list
        data_to_return['precision_list'] = precision_list
        data_to_return['recall_list'] = recall_list
    else:
        data_to_return['spearmanr_list'] = spearmanr_list
        data_to_return['y_testing_list'] = y_testing_list
        data_to_return['y_predicted_list'] = y_predicted_list
 

    return data_to_return


#
# example
#
def example():
    import pandas as pd
    import pprint as pp

    formula = 'y_bin ~ C(base_05_from_PAM) + C(base_18_from_PAM) + C(base_20_from_PAM) + C(base_07_from_PAM) + C(base_04_from_PAM) + C(base_15_from_PAM) + C(base_12_from_PAM) + C(base_01_from_PAM) + C(base_10_from_PAM) + C(base_03_from_PAM) + C(base_02_from_PAM) + C(pam) + be_seed_6 + se_full + se_seed_5 + folding_dG + motif_scores'

    df = pd.read_csv('../../crispr/crc/efficiency_scoring_model/output/df_for_modeling.csv')


    idx_to_keep = [i for i, x in enumerate(df['y']) if x >= 2./3. or x <= 1./3.]
    df_sectioned = df.iloc[idx_to_keep,].copy()

    y_bin_list = []
    for y in df_sectioned['y']:
        if y >= 2./3:
            y_bin_list.append(1.)
        if y <= 1./3.:
            y_bin_list.append(0.)
    df_sectioned['y_bin'] = y_bin_list

    results = v_fold(logit_wrapper, df_sectioned, 2, formula)
    pp.pprint(results)


    print
    print

    formula = 'y ~ C(base_05_from_PAM) + C(base_18_from_PAM) + C(base_20_from_PAM) + C(base_07_from_PAM) + C(base_04_from_PAM) + C(base_15_from_PAM) + C(base_12_from_PAM) + C(base_01_from_PAM) + C(base_10_from_PAM) + C(base_03_from_PAM) + C(base_02_from_PAM) + C(pam) + be_seed_6 + se_full + se_seed_5 + folding_dG + motif_scores'

    df = pd.read_csv('../../crispr/crc/efficiency_scoring_model/output/df_for_modeling.csv')
    results = v_fold(random_forest_regression_wrapper, df_sectioned, 3, formula, n_jobs=10, classification=False)
    pp.pprint(results)


#
# plot AUC Histogram
#
def plot_auc_histogram(results_from_v_fold, title, output_file):
    auc_list = results_from_v_fold['auc_list']
    plt.figure()
    plt.hist(auc_list, color='purple')
    plt.title(title)
    plt.xlabel('Area Under ROC Curve')
    plt.ylabel('Frequency')
    plt.savefig(output_file)
    plt.close()


#
# get a representative ROC plot
#
def plot_a_representative_ROC_plot(results_from_v_fold, title, output_file):
    info_dict = {
        'auc_list' : results_from_v_fold['auc_list'],
        'fpr_list' : results_from_v_fold['fpr_list'],
        'tpr_list' : results_from_v_fold['tpr_list'],
    }
    sorted_dict = sort_lists_by_rank_of_another_list(info_dict, 'auc_list')
    i = int(round(float(len(sorted_dict['auc_list'])) / 2.))
    fpr = sorted_dict['fpr_list'][i]
    tpr = sorted_dict['tpr_list'][i]
    roc_auc = sorted_dict['auc_list'][i]

    plt.figure()
    plt.plot(fpr, tpr, color='darkorange', lw=2, label='ROC Curve (Area = %0.2f)' % roc_auc)
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend(loc="lower right")
    plt.savefig(output_file)
    plt.close()



def output_libsvm_unscaled_from_df(df, formula, output_file, classification=False):
    y, X = dmatrices(formula, df, return_type = 'dataframe')
    output_libsvm_unscaled_from_y_X(y, X, formula, output_file, classification=classification)

def output_libsvm_unscaled_from_y_X(y, X, output_file, classification=False):

    if 'Intercept' in list(X.columns.values):
        del X['Intercept']

    f = open(output_file, 'w')
    for i, y_value in zip(range(0, len(y)), y.iloc[:,0]):
        
        if classification:
            y_value = int(y_value)
            if y_value == 0:
                y_value = -1

        line = []
        for name_idx, name in enumerate(sorted(list(X.columns.values))):
            line.append(X.iloc[i, name_idx])

        line = [str(q + 1) + ':' + str(x) for q, x in enumerate(line)]

        final_line = [str(y_value)]

        final_line.extend(line)
        final_line = ' '.join(final_line)
        f.write(final_line + '\n')
    f.close()


def svm_scale(input_file, binary, output_file, scaling_parameters_file):
    import os
    cmd = binary + ' -s ' + scaling_parameters_file + ' ' + input_file + ' > ' + output_file
    os.system(cmd)

    


#
# SVM classification
#
class svm_wrapper(object):
    def __init__(self, y, X, c=1, g=-5, output_file='/dev/null/stuff'):
        self.c = c
        self.g = g
        self.X_header = list(X.columns.values)
        self.y_header = list(y.columns.values)
        self.output_file = output_file
        output_libsvm_unscaled_from_y_X(y, X, output_file + '.prescaled', classification=True)
        svm_scale(output_file + '.prescaled', '/rhome/emily/packages/libsvm-3.22/svm-scale', output_file + '.scaled', output_file + '.scaling_parameters')

        cmd = '/rhome/emily/packages/libsvm-3.22/svm-train' + ' -g ' + str(g) + ' -c ' + str(c) + ' -b 1 ' + output_file + '.scaled' + ' ' + output_file + '.model'
        import os
        os.system(cmd)

    def predict(self, X):

        output_file = '/tmp/SVM_' + str(uuid.uuid4())

        import os
        y = pd.DataFrame([1] * len(X))

        output_libsvm_unscaled_from_y_X(y, X, output_file + '.prescaled_to_predict', classification=True)


        cmd = '/rhome/emily/packages/libsvm-3.22/svm-scale' + ' -r ' + self.output_file + '.scaling_parameters' + ' ' + output_file + '.prescaled_to_predict' + ' > ' + output_file + '.scaled_to_predict'
        os.system(cmd)

        cmd = '/rhome/emily/packages/libsvm-3.22/svm-predict' + ' -b 1 ' + output_file + '.scaled_to_predict' + ' ' + self.output_file + '.model' + ' ' + output_file + '.predicted'

        os.system(cmd)
        f = open(output_file + '.predicted')
        y_predicted = []
        for line in f:
            line = line.strip()
            if line.find('labels') >= 0:  continue
            y_value = float(line.split(' ')[1])
            y_predicted.append(y_value)
        f.close()
        os.system('rm ' + output_file + '*')
        return y_predicted


#
# SVM regression
#
class svm_regression_wrapper(object):
    def __init__(self, y, X, c=1, g=-5, e=0.1, output_file='/dev/null/stuff'):
        self.c = c
        self.g = g
        self.e = e
        self.X_header = list(X.columns.values)
        self.y_header = list(y.columns.values)
        self.output_file = output_file
        output_libsvm_unscaled_from_y_X(y, X, output_file + '.prescaled')
        svm_scale(output_file + '.prescaled', '/rhome/emily/packages/libsvm-3.22/svm-scale', output_file + '.scaled', output_file + '.scaling_parameters')

        cmd = '/rhome/emily/packages/libsvm-3.22/svm-train' + ' -s 3 -g ' + str(g) + ' -c ' + str(c) + ' -p ' + str(e) + ' ' + output_file + '.scaled' + ' ' + output_file + '.model'
        import os
        os.system(cmd)

    def predict(self, X):

        output_file = '/tmp/SVM_' + str(uuid.uuid4())

        import os
        y = pd.DataFrame([1] * len(X))

        output_libsvm_unscaled_from_y_X(y, X, output_file + '.prescaled_to_predict')


        cmd = '/rhome/emily/packages/libsvm-3.22/svm-scale' + ' -r ' + self.output_file + '.scaling_parameters' + ' ' + output_file + '.prescaled_to_predict' + ' > ' + output_file + '.scaled_to_predict'
        os.system(cmd)

        cmd = '/rhome/emily/packages/libsvm-3.22/svm-predict' + ' ' + output_file + '.scaled_to_predict' + ' ' + self.output_file + '.model' + ' ' + output_file + '.predicted'
        os.system(cmd)

        f = open(output_file + '.predicted')
        y_predicted = []
        for line in f:
            line = line.strip()
            if line.find('labels') >= 0:  continue
            y_value = float(line)
            y_predicted.append(y_value)
        f.close()
        os.system('rm ' + output_file + '*')
        return y_predicted




#
# deal with categorization
#
def categorize(formula, factor_options, df, add_intercept=True):
    y_side = [x.strip() for x in formula.split('~')[0].strip().split('+')]
    x_side = [x.strip() for x in formula.split('~')[1].strip().split('+')]

    # build y
    y_dict = {}
    for name in y_side:
        y_dict[name] = list(df[name])
    df_y = pd.DataFrame(y_dict)

    # build x
    x_dict = {}
    for name in x_side:
        if name.find('C(') != 0:
            x_dict[name] = list(df[name])
        else:
            name = name[2:-1]
            potential_factor_list = sorted(factor_options[name])[1:]
            for p in potential_factor_list:
                x_dict[name + '_is_' + p] = []
            for i in df[name]:
                for p in potential_factor_list:
                    if i == p:
                        x_dict[name + '_is_' + p].append(1.)
                    else:
                        x_dict[name + '_is_' + p].append(0.)
    df_x = pd.DataFrame(x_dict)
    
    if add_intercept:
        df_x['Intercept'] = 1.

    return df_y, df_x
