#
# load useful libraries
#
import pickle
from statsmodels.tsa.stattools import grangercausalitytests
from numpy import NaN, mean
from math import log
import pprint as pp
import glob
import json
import pandas as pd

#
# user settings
#
output_directory = 'output'
quote_data_directory = 'quote_data'
threshold = 0.05
number_of_lags = 5
###run_self_volume_to_adj_close = False
run_NxN_volume_to_adj_close = True

#
# get symbol list
#
symbol_list = sorted([x.split('/')[1].replace('.pickle', '') for x in glob.glob(quote_data_directory + '/*.pickle')])

#
# function to load and prepare stock data
#
def load_and_prepare_stock_data(symbol):
    with open(quote_data_directory + '/' + symbol + '.pickle') as f:
        df = pickle.load(f)
    percent_diff = [NaN]
    percent_diff.extend( [((j - i) / i) * 100. for i, j in zip(df['Adj Close'][0:-1], df['Adj Close'][1:])] )
    df['Percent Difference Adj Close'] = percent_diff
    return df


#
# calculate causality
#
def calculate_causality(array_to_test):
    causality = grangercausalitytests(array_to_test, number_of_lags, verbose=False)

    lag_dict = {}
    for lag in sorted(causality.keys()):
        tests = causality[lag][0]
        p_list = []
        for t in tests.keys():
            p = tests[t][1]
            p_list.append(p)

        mean_p_list = mean(p_list)
        if mean_p_list <= threshold:
            log_mean_p_list = log(mean_p_list, 10.)
            log_mean_p_list_str = '%0.2f' % log_mean_p_list
            lag_dict[lag] = float(log_mean_p_list_str)
    return lag_dict

# #
# # selfwise comparisons
# #
# self_causality = {}
# if run_self_volume_to_adj_close:
#     for symbol in symbol_list:
#         df = load_and_prepare_stock_data(symbol)
#         array_to_test = df.ix[1:, ['Percent Difference Adj Close', 'Volume']].as_matrix()
#         try:
#             results = calculate_causality(array_to_test)
#             if results != {}:
#                 self_causality[symbol] = results
#         except:
#             continue

#     #
#     # save self_causality
#     #
#     with open(output_directory + '/self_causality.json', 'w') as f:
#         json.dump(self_causality, f)




#
# pairwise comparisons
#
pairwise_causality = {}

#break_all = False

if run_NxN_volume_to_adj_close:
    for i in symbol_list:

        print i

        for j in symbol_list:

            df_i = load_and_prepare_stock_data(i)
            df_j = load_and_prepare_stock_data(j)

            df = pd.merge(df_i, df_j, left_index=True, right_index=True)

            for col in [
                'Open_x', 'High_x', 'Low_x', 'Close_x', 'Adj Close_x', 'Volume_x',
                'Open_y', 'Close_y', 'High_y', 'Low_y', 'Adj Close_y', 'Percent Difference Adj Close_y']:
                del(df[col])

            array_to_test = df.ix[1:, :].as_matrix()

            try:
                results = calculate_causality(array_to_test)
                if results != {}:

                    #break_all = True

                    if not pairwise_causality.has_key(i):
                        pairwise_causality[i] = {}
                    pairwise_causality[i][j] = results
            except:
                continue

        #if break_all:
        #    break

    #
    # save pairwise causalitity
    #
    with open(output_directory + '/pairwise_causality.json', 'w') as f:
        json.dump(pairwise_causality, f)


