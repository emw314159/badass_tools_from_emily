#
# load useful libraries
#
import pickle
import glob
import pprint as pp
from numpy import NaN, percentile, isnan
import matplotlib.pyplot as plt
from datetime import timedelta
from neo4j.v1 import GraphDatabase, basic_auth
import pandas as pd

import statsmodels.api as sm
import itertools

from scipy.stats import spearmanr

#
# user settings
#
output_directory = 'output'
quote_data_directory = 'quote_data'
volume_threshold = 500000
database_lags = 2
calculate_events = False
calculate_database = False
calculate_match = True

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
dt_plus_1_day = timedelta(days=1)
dt_plus_2_day = timedelta(days=2)
symbols_with_event = {}

if calculate_events:
    events = []
    for symbol in symbol_list[0:200]:
        df = load_and_prepare_stock_data(symbol)
        start_date = df.index[0]
        end_date = df.index[-1]
        idx = df.ix[df['Percent Difference Volume'] >= volume_threshold, :].index
        for i in idx:
            symbols_with_event[symbol] = None
            if i >= end_date + dt_1_day:  continue
            if i + dt_52_week < start_date:  continue

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

            events.append({
                    'volume_ts' : ts,
                    'volume_percent_diff_volume' : df.ix[i,:]['Percent Difference Volume'],
                    'volume_symbol' : symbol,
                    'weekday' : weekday_map[weekday],
                    'volume_percent_52_week_high' : percent_52_week_high,
                    'volume_percent_12_week_high' : percent_12_week_high,
                    'volume_percent_4_week_high' : percent_4_week_high,
                    'volume_lag_0' : lag_0,
                    'volume_lag_1' : lag_1,
                    'volume_lag_2' : lag_2,
                    'volume_lag_3' : lag_3,
                    'volume_lag_4' : lag_4,
                    'volume_lag_5' : lag_5,
                    'date' : i,
                    })

    with open(output_directory + '/events.pickle', 'w') as f:
        pickle.dump(events, f)
    with open(output_directory + '/symbols_with_events.pickle', 'w') as f:
        pickle.dump(symbols_with_event, f)

else:
    with open(output_directory + '/events.pickle') as f:
        events = pickle.load(f)
    with open(output_directory + '/symbols_with_events.pickle') as f:
        symbols_with_event = pickle.load(f)




#
# get content from database
#
if calculate_database:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
    session = driver.session()
    database_content = {}
    for symbol in sorted(symbols_with_event.keys()):

        cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY), (volume)-[rvs:HAS_SECTOR]-(vs:SECTOR), (close)-[rcs:HAS_SECTOR]-(cs:SECTOR), (volume)-[rvi:HAS_INDUSTRY]-(vi:INDUSTRY), (close)-[rci:HAS_INDUSTRY]-(ci:INDUSTRY) WHERE r.lag = ' + str(database_lags) + ' AND volume.id = \'' + symbol + '\' RETURN volume.id AS volume, close.id AS close, r.p_log_10 AS p_log_10, vs.sector AS volume_sector, cs.sector AS close_sector, vi.industry AS volume_industry, ci.industry AS close_industry;'
        
        #cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY) WHERE r.lag = ' + str(database_lags) + ' AND volume.id = \'' + symbol + '\' RETURN volume.id AS volume, close.id AS close, r.p_log_10 AS p_log_10;'

        result = session.run(cmd)

        for record in result:
            volume = record['volume']
            if not database_content.has_key(volume):
                database_content[volume] = []
            database_content[volume].append({
                    'close' : record['close'],
                    'p_log_10' : record['p_log_10'],
                    'volume_sector' : record['volume_sector'],
                    'close_sector' : record['close_sector'],
                    'volume_industry' : record['volume_industry'],
                    'close_industry' : record['close_industry'],
                    })

    with open(output_directory + '/database_content.pickle', 'w') as f:
        pickle.dump(database_content, f)

else:
    with open(output_directory + '/database_content.pickle') as f:
        database_content = pickle.load(f)






#
# match
#
new_events = []
for e in events:
    volume = e['volume_symbol']
    if database_content.has_key(volume):
         for hit in database_content[volume]:
             new_e = e.copy() 
             for key in hit.keys():
                 new_e[key] = hit[key]
             new_events.append(new_e)


# #
# # ARIMA
# #
# def calculate_arima(y, idx):
#     # https://www.digitalocean.com/community/tutorials/a-guide-to-time-series-forecasting-with-arima-in-python-3
#     p = d = q = range(0, 2)
#     pdq = list(itertools.product(p, d, q))
#     seasonal_pdq = [(x[0], x[1], x[2], 12) for x in list(itertools.product(p, d, q))]
#     param_dict = {}
#     for param in pdq:
#         for param_seasonal in seasonal_pdq:
#             try:
#                 mod = sm.tsa.statespace.SARIMAX(y,
#                                                 order=param,
#                                                 seasonal_order=param_seasonal,
#                                                 enforce_stationarity=False,
#                                                 enforce_invertibility=False)
                
#                 results = mod.fit()

#                 param_dict[results.aic] = {
#                     'param' : param,
#                     'param_seasonal' : param_seasonal,
#                     }
#             except:
#                 continue

#     if param_dict == {}:
#         return None, None

#     aic = sorted(param_dict.keys())[0]
#     param = param_dict[aic]['param']
#     param_seasonal = param_dict[aic]['param_seasonal']

#     mod = sm.tsa.statespace.SARIMAX(y,
#                                     order=param,
#                                     seasonal_order=param_seasonal,
#                                     enforce_stationarity=False,
#                                     enforce_invertibility=False,
#                                     verbose=False)
    
#     results = mod.fit()

#     start = pd.to_datetime(str(idx.date()))
#     end = pd.to_datetime(str((idx + dt_plus_2_day).date()))

#     try:
#         pred = results.get_prediction(dynamic=False, start=start, end=end)
#         return pred.predicted_mean[1], pred.predicted_mean[2]
#     except:
#         return None, None


#
# function for Spearman's R
#
def add_spearman_r(i_dict):
#     close_list = [
#         i_dict['close_lag_5'],
#         i_dict['close_lag_4'],
#         i_dict['close_lag_3'],
#         i_dict['close_lag_2'],
#         i_dict['close_lag_1'],
#         i_dict['close_lag_0'],
#         ]
#     volume_list = [
#         i_dict['volume_lag_5'],
#         i_dict['volume_lag_4'],
#         i_dict['volume_lag_3'],
#         i_dict['volume_lag_2'],
#         i_dict['volume_lag_1'],
#         i_dict['volume_lag_0'],
#         ]
#     spr, p = spearmanr(close_list, volume_list)

    if i_dict['volume_symbol'] == i_dict['close']:
        spr = 1.
        p = 0.
    else:
        spr, p = spearmanr(i_dict['volume_ts'], i_dict['close_ts'])

    i_dict['spearman_r'] = spr
    i_dict['spearman_r_p'] = p

#
# connect to close data
#
if calculate_match:
    close_map = {}
    for e in new_events:
        close = e['close']
        if not close_map.has_key(close):
            close_map[close] = []
        close_map[close].append({'date' : e['date'], 'found' : False})

    for close in close_map.keys():
        df = load_and_prepare_stock_data(close)
        start_date = df.index[0]
        end_date = df.index[-1]

        for i_dict in close_map[close]:
            idx = i_dict['date']
            if idx >= end_date + dt_1_day:  continue
            if idx + dt_52_week < start_date:  continue
            i_dict['found'] = True

            percent_52_week_high = df.ix[idx,:]['Adj Close'] / max(df.ix[(idx+dt_52_week):(idx+dt_1_day),:]['Adj Close'])
            percent_12_week_high = df.ix[idx,:]['Adj Close'] / max(df.ix[(idx+dt_12_week):(idx+dt_1_day),:]['Adj Close'])
            percent_4_week_high = df.ix[idx,:]['Adj Close'] / max(df.ix[(idx+dt_4_week):(idx+dt_1_day),:]['Adj Close'])

            ts = df.ix[(idx+dt_4_week):(idx+dt_1_day)]['Percent Difference Adj Close']

            loc = list(df.index).index(idx)
            lead_1 = df.ix[df.index[loc + 1],:]['Percent Difference Adj Close']
            lead_2 = df.ix[df.index[loc + 2],:]['Percent Difference Adj Close']
            lag_0 = df.ix[df.index[loc - 0],:]['Percent Difference Adj Close']
            lag_1 = df.ix[df.index[loc - 1],:]['Percent Difference Adj Close']
            lag_2 = df.ix[df.index[loc - 2],:]['Percent Difference Adj Close']
            lag_3 = df.ix[df.index[loc - 3],:]['Percent Difference Adj Close']
            lag_4 = df.ix[df.index[loc - 4],:]['Percent Difference Adj Close']
            lag_5 = df.ix[df.index[loc - 5],:]['Percent Difference Adj Close']

            #arima_30_lead_1, arima_30_lead_2 = calculate_arima( df.ix[(idx+dt_4_week):idx,:]['Percent Difference Adj Close'], idx )


            i_dict['close_ts'] = ts
            i_dict['close_percent_diff_volume'] = df.ix[idx,:]['Percent Difference Volume']
            i_dict['close_percent_52_week_high'] = percent_52_week_high
            i_dict['close_percent_12_week_high'] = percent_12_week_high
            i_dict['close_percent_4_week_high'] = percent_4_week_high
            i_dict['close_lead_1'] = lead_1
            i_dict['close_lead_2'] = lead_2
            i_dict['close_lag_0'] = lag_0
            i_dict['close_lag_1'] = lag_1
            i_dict['close_lag_2'] = lag_2
            i_dict['close_lag_3'] = lag_3
            i_dict['close_lag_4'] = lag_4
            i_dict['close_lag_5'] = lag_5
            #i_dict['close_arima_30_lead_1'] = arima_30_lead_1
            #i_dict['close_arima_30_lead_2'] = arima_30_lead_2




    events_to_scrap = []
    for eidx, e in enumerate(new_events):
        date = e['date']
        close = e['close']
        matched = False
        if close_map.has_key(close):
            for i_dict in close_map[close]:
                if i_dict['date'] == date:
                    if i_dict['found']:
                        for key in i_dict.keys():
                            if not key in ['date', 'found']:
                                e[key] = i_dict[key]
                            matched = True
        if not matched:
            events_to_scrap.append(eidx)

    final_events = []
    for eidx, e in enumerate(new_events):
        if not eidx in events_to_scrap:

            #
            # Add spearman here
            #
            add_spearman_r(e)



            if not isnan(e['spearman_r']):
                final_events.append(e)


    #
    # save dataframe
    #
    for e in final_events:
        del(e['volume_ts'])
        del(e['close_ts'])
    df = pd.DataFrame(final_events)
    df.to_csv(output_directory + '/data_for_model.csv', index=False)



#
# load dataframe
#
df = pd.read_csv(output_directory + '/data_for_model.csv')

#
# add some similarity variables
#
for e in final_events:
    e['same_industry'] = int(e['close_industry'] == e['volume_industry'])
    e['same_sector'] = int(e['close_sector'] == e['volume_sector'])
    e['same_stock'] = int(e['close'] == e['volume_symbol'])


#
# save dataframe
#
df = pd.DataFrame(final_events)
df.to_csv(output_directory + '/data_for_model.csv', index=False)



#
# output index length
#
print
print 'There are ' + str(len(df.index)) + ' entries in the dataframe.'
print













