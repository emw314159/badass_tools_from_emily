#
# load useful libraries
#
import pickle
import pprint as pp
import datetime
from neo4j.v1 import GraphDatabase, basic_auth
import pandas as pd
import json
import pandas_datareader as pdr
from numpy import NaN
import sys

from badass_tools_from_emily.misc import chunk

#
# user settings
#
user = 'neo4j'
password = 'aoeuI444'
volume_threshold = 500000
database_lags = 2
runtime_output_directory = 'output'
runtime_output_directory_year = 'output/year'
query_database_for_movers = False
get_two_day_stocks = False
pull_year_for_volume_and_close = False
calculate_feature_for_symbols = False

# this is repeated code
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
# connect to database
#
driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
session = driver.session()

#
# establish yesterday's date
#
end = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()

#
# get volume movers known to database
#
if query_database_for_movers:
    cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY) WHERE r.lag = ' + str(database_lags) + ' RETURN volume.id AS volume, close.id AS close, r.lag as lag, r.p_log_10 as p_log_10;'
    volume_movers = {}
    result = session.run(cmd)
    for record in result:
        volume = record['volume']
        close = record['close']
        lag = str(record['lag'])
        p_log_10 = record['p_log_10']

        if not volume_movers.has_key(volume):
            volume_movers[volume] = {}
        if not volume_movers[volume].has_key(close):
            volume_movers[volume][close] = p_log_10

    with open(runtime_output_directory + '/volume_movers.json', 'w') as f:
        json.dump(volume_movers, f)

else:
    with open(runtime_output_directory + '/volume_movers.json') as f:
        volume_movers = json.load(f)




#
#
#
def f(volume_list, n, start, end, volumes_that_moved_yesterday):

    errors = []
    chunks = chunk(volume_list, n)
    
    print
    print len(chunks)
    print

    for i, c in enumerate(chunks):

        print i

        try:
            panel = pdr.get_data_yahoo(symbols=c, start=start, end=end)
            
            for symbol in c:
                df = panel.minor_xs(symbol)
                df = df.sort_index()
                d_volume = [(100. * (j - i) / i) for i, j in zip(df['Volume'][0:-1], df['Volume'][1:])]
                if d_volume[-1] >= volume_threshold:
                    volumes_that_moved_yesterday.append(symbol)
        except:
            errors.extend(c)
    
    return errors


#
# get two day stocks
#
volumes_that_moved_yesterday = []
if get_two_day_stocks:
    volume_list = sorted(volume_movers.keys())
    start = (end + datetime.timedelta(days=-8))

    errors = f(volume_list, 200, start, end, volumes_that_moved_yesterday)
    print
    print 'length(errors) = ' + str(len(errors)) + '\t' + str(len(volumes_that_moved_yesterday))
    print

    errors = f(errors, 10, start, end, volumes_that_moved_yesterday)
    print
    print 'length(errors) = ' + str(len(errors)) + '\t' + str(len(volumes_that_moved_yesterday))
    print

    errors = f(errors, 1, start, end, volumes_that_moved_yesterday)
    print
    print 'length(errors) = ' + str(len(errors)) + '\t' + str(len(volumes_that_moved_yesterday))
    print


    with open(runtime_output_directory + '/volumes_that_moved_yesterday.json', 'w') as f:
        json.dump(volumes_that_moved_yesterday, f)

else:
    with open(runtime_output_directory + '/volumes_that_moved_yesterday.json') as f:
        volumes_that_moved_yesterday = json.load(f)







#
#
#
def f2(stock_list, n, start, end):

    errors = []
    chunks = chunk(stock_list, n)
    
    print
    print len(chunks)
    print

    for i, c in enumerate(chunks):

        print i

        try:
            panel = pdr.get_data_yahoo(symbols=c, start=start, end=end)
            
            for symbol in c:
                df = panel.minor_xs(symbol)
                df = df.sort_index()
                with open(runtime_output_directory_year + '/' + symbol + '.pickle', 'w') as f:
                    pickle.dump(df, f)
        except:
            errors.extend(c)
    
    return errors


#
# pull year for volumes, close for volumes that moved
#
if pull_year_for_volume_and_close:
    unique_symbols = {}
    for volume in volumes_that_moved_yesterday:
        unique_symbols[volume] = None
        for close in volume_movers[volume].keys():
            unique_symbols[close] = None

    start = (end + datetime.timedelta(days=-380))

    errors = f2(unique_symbols.keys(), 200, start, end)
    print
    print 'length(errors) = ' + str(len(errors))
    print

    errors = f2(errors, 10, start, end)
    print
    print 'length(errors) = ' + str(len(errors))
    print

    errors = f2(errors, 1, start, end)
    print
    print 'length(errors) = ' + str(len(errors))
    print

    with open(runtime_output_directory + '/unique_symbols.json', 'w') as f:
        json.dump(unique_symbols, f)

else:
    with open(runtime_output_directory + '/unique_symbols.json') as f:
        unique_symbols = json.load(f)



#
# function to load and prepare stock data
#
#
# This is almost the same as in model_part_01.py
#
def load_and_prepare_stock_data(symbol, directory):
    with open(directory + '/' + symbol + '.pickle') as f:
        df = pickle.load(f)
    df = df.sort_index()
    percent_diff = [NaN]
    percent_diff.extend( [((j - i) / i) * 100. for i, j in zip(df['Adj Close'][0:-1], df['Adj Close']
[1:])] )
    df['Percent Difference Adj Close'] = percent_diff
    percent_diff = [NaN]
    percent_diff.extend( [((j - i + 1) / (i + 1)) * 100. for i, j in zip(df['Volume'][0:-1], df['Volume'][1:])] )
    df['Percent Difference Volume'] = percent_diff
    return df




#
# calculate features for each unique symbol
#
dt_52_week = datetime.timedelta(days=-365)
dt_4_week = datetime.timedelta(days=-28)
dt_12_week = datetime.timedelta(days=-84)
dt_1_day = datetime.timedelta(days=-1)
dt_plus_1_day = datetime.timedelta(days=1)
dt_plus_2_day = datetime.timedelta(days=2)

if calculate_feature_for_symbols:
    calculated_features = {}
    for symbol in unique_symbols.keys():
        df = load_and_prepare_stock_data(symbol, runtime_output_directory_year)

        end_dt = datetime.datetime(end.year, end.month, end.day)
        idx = df.ix[df.index <= end_dt, :].index
        i = idx[-1]

        percent_52_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_52_week):(i+dt_1_day),:]['Adj Close'])
        percent_12_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_12_week):(i+dt_1_day),:]['Adj Close'])
        percent_4_week_high = df.ix[i,:]['Adj Close'] / max(df.ix[(i+dt_4_week):(i+dt_1_day),:]['Adj Close'])

        ts = df.ix[(i+dt_4_week):(i+dt_1_day)]['Percent Difference Adj Close']

        loc = list(df.index).index(i)
        weekday = i.weekday()
        lag_0 = df.ix[df.index[loc - 0],:]['Percent Difference Adj Close']
        lag_1 = df.ix[df.index[loc - 1],:]['Percent Difference Adj Close']
        lag_2 = df.ix[df.index[loc - 2],:]['Percent Difference Adj Close']
        lag_3 = df.ix[df.index[loc - 3],:]['Percent Difference Adj Close']
        lag_4 = df.ix[df.index[loc - 4],:]['Percent Difference Adj Close']
        lag_5 = df.ix[df.index[loc - 5],:]['Percent Difference Adj Close']

        cmd = 'MATCH (c:COMPANY)-[rs:HAS_SECTOR]-(s:SECTOR), (c:COMPANY)-[ri:HAS_INDUSTRY]-(i:INDUSTRY) WHERE c.id = \'' + symbol + '\' RETURN c.id AS company, i.id AS industry, s.id AS sector;'

        result = session.run(cmd)
        for record in result:
            count += 1
            industry = record['industry']
            sector = record['sector']

        calculated_features[symbol] = {
            'percent_diff_volume' : df.ix[i,:]['Percent Difference Volume'],
            'percent_52_week_high' : percent_52_week_high,
            'percent_12_week_high' : percent_12_week_high,
            'percent_4_week_high' : percent_4_week_high,
            'ts' : list(ts),
            'weekday' : weekday_map[weekday],
            'lag_0' : lag_0, 
            'lag_1' : lag_1, 
            'lag_2' : lag_2, 
            'lag_3' : lag_3, 
            'lag_4' : lag_4, 
            'lag_5' : lag_5, 
            'industry' : industry,
            'sector' : sector,
            'date' : str(i.year) + '-' + str(i.month) + '-' + str(i.day),
        }


    with open(runtime_output_directory + '/calculated_features.json', 'w') as f:
        json.dump(calculated_features, f)

else:
    with open(runtime_output_directory + '/calculated_features.json') as f:
        calculated_features = json.load(f)

pp.pprint(calculated_features)

