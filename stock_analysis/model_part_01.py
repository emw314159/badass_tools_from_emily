#
# load useful libraries
#
import pickle
import glob
import pprint as pp
from numpy import NaN, percentile
import matplotlib.pyplot as plt
from datetime import timedelta
from neo4j.v1 import GraphDatabase, basic_auth

#
# user settings
#
output_directory = 'output'
quote_data_directory = 'quote_data'
volume_threshold = 1000000
database_lags = 2
calculate_events = False
calculate_database = False

user = 'neo4j'
password = 'aoeuI111'

weekday_map = {
    0 : 'M',
    1 : 'Tu',
    2 : 'W',
    3 : 'Th',
    4 : 'F',
    5 : 'Sa',
    6 : 'Su',
}

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
symbols_with_event = {}

if calculate_events:
    events = []
    for symbol in symbol_list[0:15]:
        df = load_and_prepare_stock_data(symbol)
        start_date = df.index[0]
        end_date = df.index[-1]
        idx = df.ix[df['Percent Difference Volume'] >= volume_threshold, :].index
        for i in idx:
            symbols_with_event[symbol] = None
            if i == end_date:  continue
            if i + dt_52_week < start_date:  continue

            percent_52_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_52_week):(i+dt_1_day),:]['Adj Close'])
            percent_12_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_12_week):(i+dt_1_day),:]['Adj Close'])
            percent_4_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_4_week):(i+dt_1_day),:]['Adj Close'])

            loc = list(df.index).index(i)
            weekday = i.weekday()
            lag_0 = df.ix[df.index[loc - 0],:]['Percent Difference Adj Close']
            lag_1 = df.ix[df.index[loc - 1],:]['Percent Difference Adj Close']
            lag_2 = df.ix[df.index[loc - 2],:]['Percent Difference Adj Close']
            lag_3 = df.ix[df.index[loc - 3],:]['Percent Difference Adj Close']
            lag_4 = df.ix[df.index[loc - 4],:]['Percent Difference Adj Close']
            lag_5 = df.ix[df.index[loc - 5],:]['Percent Difference Adj Close']

            events.append({
                    'mover_percent_diff_volume' : df.ix[i,:]['Percent Difference Volume'],
                    'mover_symbol' : symbol,
                    'weekday' : weekday_map[weekday],
                    'mover_percent_52_week_high' : percent_52_week_high,
                    'mover_percent_12_week_high' : percent_12_week_high,
                    'mover_percent_4_week_high' : percent_4_week_high,
                    'mover_lag_0' : lag_0,
                    'mover_lag_1' : lag_1,
                    'mover_lag_2' : lag_2,
                    'mover_lag_3' : lag_3,
                    'mover_lag_4' : lag_4,
                    'mover_lag_5' : lag_5,
                    'date' : i,
                    })

    with open(output_directory + '/events.pickle', 'w') as f:
        pickle.dump(events, f)
    with open(output_directory + '/symbols_with_events.pickle', 'w') as f:
        pickle.dump(symbols_with_events, f)

else:
    with open(output_directory + '/events.pickle') as f:
        events = pickle.load(f)
    with open(output_directory + '/symbols_with_events.pickle') as f:
        symbols_with_event = pickle.load(f)

#
# get content from database
#
driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
session = driver.session()

if calculate_database:
    for symbol in symbols_with_event[0:15]:
        cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY) WHERE r.lag = ' + str(database_lag) + ' AND volume.id = ' + symbol + ' RETURN volume.id AS volume, close.id AS close, r.p_log_10 AS p_log_10;'
        result = session.run(cmd)

        print
        print result








