#
# load useful libraries
#
import pickle
import glob
import pprint as pp
from numpy import NaN, percentile
import matplotlib.pyplot as plt
from datetime import timedelta

#
# user settings
#
output_directory = 'output'
quote_data_directory = 'quote_data'
volume_threshold = 1000000
calculate_events = True

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
# get symbol list
#
symbol_list = sorted([x.split('/')[1].replace('.pickle', '') for x in glob.glob(quote_data_directory + '/*.pickle')])

#
# figure out dates of event
#
dt_52_week = timedelta(days=-365)
dt_4_week = timedelta(days=-28)
dt_12_week = timedelta(days=-84)
dt_1_day = timedelta(days=-1)

if calculate_events:
    events = []
    for symbol in symbol_list:
        df = load_and_prepare_stock_data(symbol)
        start_date = df.index[0]
        end_date = df.index[-1]
        idx = df.ix[df['Percent Difference Volume'] >= volume_threshold, :].index
        for i in idx:
            if i == end_date:  continue
            if i + dt_52_week < start_date:  continue

            percent_52_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_52_week):(i+dt_1_day),:]['Adj Close'])
            percent_12_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_12_week):(i+dt_1_day),:]['Adj Close'])
            percent_4_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_4_week):(i+dt_1_day),:]['Adj Close'])

            loc = list(df.index).index(i)
            weekday = i.weekday()
            lag_1 = df.ix[df.index[loc - 1],:]['Percent Difference Adj Close']
            lag_2 = df.ix[df.index[loc - 2],:]['Percent Difference Adj Close']
            lag_3 = df.ix[df.index[loc - 3],:]['Percent Difference Adj Close']
            lag_4 = df.ix[df.index[loc - 4],:]['Percent Difference Adj Close']
            lag_5 = df.ix[df.index[loc - 5],:]['Percent Difference Adj Close']

            events.append({
                    'mover_percent_diff_volume' : df.ix[i,:]['Percent Difference Volume'],
                    'mover_symbol' : symbol,
                    'weekday' : weekday,
                    'mover_percent_52_week_high' : percent_52_week_high,
                    'mover_percent_12_week_high' : percent_12_week_high,
                    'mover_percent_4_week_high' : percent_4_week_high,
                    'mover_lag_1' : lag_1,
                    'mover_lag_2' : lag_2,
                    'mover_lag_3' : lag_3,
                    'mover_lag_4' : lag_4,
                    'mover_lag_5' : lag_5,
                    'date' : i,
                    })

    with open(output_directory + '/events.pickle', 'w') as f:
        pickle.dump(events, f)

else:
    with open(output_directory + '/events.pickle') as f:
        events = pickle.load(f)









