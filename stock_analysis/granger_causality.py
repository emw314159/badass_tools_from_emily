#
# load useful libraries
#
import pickle
from statsmodels.tsa.stattools import grangercausalitytests
from numpy import NaN, mean
import pprint as pp
import glob
import json

#
# user settings
#
output_directory = 'output'
quote_data_directory = 'quote_data'
threshold = 0.05
number_of_lags = 5
run_self_volume_to_adj_close = True


#
# get symbol list
#
symbol_list = [x.split('/')[1].replace('.pickle', '') for x in glob.glob(quote_data_directory + '/*.pickle')]

#
# iterate through symbols
#
self_causality = {}
if run_self_volume_to_adj_close:
    for symbol in symbol_list:

        with open(quote_data_directory + '/' + symbol + '.pickle') as f:
            df = pickle.load(f)

        percent_diff = [NaN]
        percent_diff.extend( [((j - i) / i) * 100. for i, j in zip(df['Adj Close'][0:-1], df['Adj Close'][1:])] )

        df['Percent Difference Adj Close'] = percent_diff

        array_to_test = df.ix[1:, ['Percent Difference Adj Close', 'Volume']].as_matrix()

        try:
            causality = grangercausalitytests(array_to_test, number_of_lags, verbose=False)

            for lag in sorted(causality.keys()):
                tests = causality[lag][0]
                p_list = []
                for t in tests.keys():
                    p = tests[t][1]
                    p_list.append(p)
                    
                mean_p_list = mean(p_list)
                if mean_p_list <= threshold:

                    if not self_causality.has_key(symbol):
                        self_causality[symbol] = {}

                    mean_p_list_str = '%0.1E' % mean_p_list
                    self_causality[symbol][lag] = float(mean_p_list_str)

        except:
            continue

    #
    # save self_causality
    #
    with open(output_directory + '/self_causality.json', 'w') as f:
        json.dump(self_causality, f)

