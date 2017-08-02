#
# what this does
#
"""
This program computes pairwise granger causality between stocks (including between a stock and itself) based on the data retrieved by "get_quotes.py". The test is whether volume granger-causes adjusted close.
"""

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
from multiprocessing import Process, Pool

#
# user settings
#
quote_data_directory = '/home/ec2-user/data/quote_data'
granger_results_directory = '/home/ec2-user/data/granger_computations'
threshold = 0.05
number_of_lags = 2
number_of_workers_in_pool = 20
chunksize = 100

#
# get list of symbols we already have computations for
#
already_have_list = sorted([x.split('/')[-1].replace('.json', '') for x in glob.glob(granger_results_directory + '/*.json')])

#
# get symbol list
#
symbol_list = sorted([x.split('/')[-1].replace('.pickle', '') for x in glob.glob(quote_data_directory + '/*.pickle')])

#
# wrapper for parallelization
#
def wrapper(ij):

    #
    # function to load and prepare stock data
    #
    def load_and_prepare_stock_data(symbol):
        with open(quote_data_directory + '/' + symbol + '.pickle') as f:
            df = pickle.load(f)
        percent_diff = [NaN]
        percent_diff.extend( [((j - i) / i) * 100. for i, j in zip(df['Adj Close'][0:-1], df['Adj Close'][1:])] )
        df['Percent Difference Adj Close'] = percent_diff
        percent_diff = [NaN]
        percent_diff.extend( [((j - i + 1) / (i + 1)) * 100. for i, j in zip(df['Volume'][0:-1], df['Volume'][1:])] )
        df['Percent Difference Volume'] = percent_diff
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


    i, j = ij
    results = {}
    try:
        df_i = load_and_prepare_stock_data(i)
        df_j = load_and_prepare_stock_data(j)
        df = pd.merge(df_i, df_j, left_index=True, right_index=True)

        for col in [
            'Open_x', 'High_x', 'Low_x', 'Close_x', 'Adj Close_x', 'Volume_x', 'Percent Difference Volume_x',
            'Open_y', 'Close_y', 'High_y', 'Low_y', 'Adj Close_y', 'Percent Difference Adj Close_y', 'Volume_y']:
            del(df[col])

        array_to_test = df.ix[1:, :].as_matrix()

        results = calculate_causality(array_to_test)

    except:
        pass
    return (i, j, results)
    

#
# pairwise comparisons
#
pool = Pool(processes=number_of_workers_in_pool)


arg_dict = {}
for i in symbol_list:
    if i in already_have_list:  continue

    arg_dict[i] = []
    for j in symbol_list:
        arg_dict[i].append((i, j,))

for symbol in sorted(arg_dict.keys()):
    arg_list = arg_dict[symbol]
    pairwise_causality = {}
    result = []

    it = pool.imap_unordered(wrapper, arg_list, chunksize=chunksize)

    current = it.next()
    while current:
        i, j, results = current
        print i, j
        if results != {}:
            pairwise_causality[j] = results
        try:
            current = it.next()
        except:
            break

    #
    # save pairwise causalitity
    #
    with open(granger_results_directory + '/' + symbol + '.json', 'w') as f:
        json.dump(pairwise_causality, f)





