
#
# import libraries
#
import pandas as pd
import pprint
import pickle
import pprint as pp
from neo4j.v1 import GraphDatabase, basic_auth
from numpy import percentile, mean
from scipy.stats import spearmanr
import datetime
from math import log

#
# user settings
#
reorganize = False
search_database = False
match = True
user = 'neo4j'
password = 'aoeuI444'
database_lags = 2
spearmanr_lags = -100
spearman_p_cutoff = 0.1

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
# reorganize
#
if reorganize:

    with open('/Users/emily/data/events.pickle') as f:
        events = pickle.load(f)

    volume_events = {}
    for e in events:
        if not volume_events.has_key(e['volume_symbol']):
            volume_events[e['volume_symbol']] = []
        volume_events[e['volume_symbol']].append(e['date'])

    with open('output/volume_events.pickle', 'w') as f:
        pickle.dump(volume_events, f)

else:
    with open('output/volume_events.pickle') as f:
        volume_events = pickle.load(f)


#
# get close for each volume
#
if search_database:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
    session = driver.session()
    database_content = {}
    volume_to_close = {}
    close_to_volume = {}
    for volume in volume_events.keys():
        volume_to_close[volume] = {}

        cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY) WHERE r.lag = ' + str(database_lags) + ' AND volume.id = \'' + volume + '\' RETURN volume.id AS volume, close.id AS close, r.p_log_10 AS p_log_10;'

        result = session.run(cmd)

        for record in result:
            close = record['close']
            p_log_10 = record['p_log_10']
            volume_to_close[volume][close] = p_log_10

            if not close_to_volume.has_key(close):
                close_to_volume[close] = {}
            close_to_volume[close][volume] = p_log_10

    
    with open('output/close_to_volume.pickle', 'w') as f:
        pickle.dump(close_to_volume, f)
    with open('output/volume_to_close.pickle', 'w') as f:
        pickle.dump(volume_to_close, f)


else:
    with open('output/close_to_volume.pickle') as f:
        close_to_volume = pickle.load(f)
    with open('output/volume_to_close.pickle') as f:
        volume_to_close = pickle.load(f)



#
# match
#
if match:

    events = []

    close_events = {}
    for close in close_to_volume.keys():
        for volume in close_to_volume[close].keys():
            close_events[close] = volume_events[volume]
    
    have_df = {}
    for close in sorted(close_events.keys()):

        print close

        if not have_df.has_key(close):
            with open('../quote_data/' + close + '.pickle') as f:
                have_df[close] = pickle.load(f)
        df_close = have_df[close]

        volume_list = []
        for volume in sorted(close_to_volume[close].keys()):
            if not have_df.has_key(volume):
                with open('../quote_data/' + volume + '.pickle') as f:
                    have_df[volume] = pickle.load(f)
            volume_list.append(volume)
    


        for ts in close_events[close]:

            close_series = df_close.ix[(ts + datetime.timedelta(days=spearmanr_lags)):(ts + datetime.timedelta(days=database_lags)),:]['Adj Close']

            volume_feature_list = []
            for volume in volume_list:
                df_volume = have_df[volume]

                volume_series = df_volume.ix[(ts + datetime.timedelta(days=spearmanr_lags)):ts,:]['Volume']
                if len(close_series) == len(volume_series) + database_lags:
                    p_log_10 = -1. * close_to_volume[close][volume]
                    
                    close_series_diff = [100. * (j - i) / (i + 1.) for i, j in zip(close_series[0:-1], close_series[1:])]
                    volume_series_diff = [100. * (j - i) / (i + 1.) for i, j in zip(volume_series[0:-1], volume_series[1:])]

                    close_lagged = close_series_diff[database_lags:]
                    volume_lagged = volume_series_diff

                    r, p = spearmanr(close_lagged, volume_lagged)
                    
                    if p > spearman_p_cutoff:
                        r = 0.
                        continue

                    #try:
                    #    sp_log_10 = -1. * log(p, 10.)
                    #except:
                    #    sp_log_10 = 0.

                    try:
                        last_volume_lagged = volume_lagged[-1]
                    except:
                        continue

                    volume_feature_list.append( p_log_10 * r * last_volume_lagged )

            if len(volume_feature_list) != 0:
                percentile_list = percentile(volume_feature_list, [0., 25., 50., 75., 100.])

                # general features
                weekday = weekday_map[ts.to_pydatetime().weekday()]
                date_for_reference = str(ts.to_pydatetime().date())

                # volume list features 
                mean_median_diff = mean(volume_feature_list) - percentile_list[2]
                p_0 = percentile_list[0]
                p_25 = percentile_list[1]
                p_50 = percentile_list[2]
                p_75 = percentile_list[3]
                p_100 = percentile_list[4]
                len_features_list = len(volume_feature_list)

                # close features
                try:
                    percent_diff_lead_1_to_lead_2 = 100. * (close_series[-1] - close_series[-2]) / close_series[-2]
                except:
                    continue

                lag_0 = close_series_diff[-3]
                lag_1 = close_series_diff[-4]
                lag_2 = close_series_diff[-5]
                lag_3 = close_series_diff[-6]
                lag_4 = close_series_diff[-7]
                lag_5 = close_series_diff[-8]
                try:
                    percent_high_year = 100. * max(df_close.ix[(ts + datetime.timedelta(days=-365)):(ts + datetime.timedelta(days=-1)),:]['Adj Close']) / df_close.ix[ts + datetime.timedelta(days=-1 * database_lags)]['Adj Close']
                    percent_high_quarter = 100. * max(df_close.ix[(ts + datetime.timedelta(days=int(-365/4))):(ts + datetime.timedelta(days=-1)),:]['Adj Close']) / df_close.ix[ts + datetime.timedelta(days=-1 * database_lags)]['Adj Close']
                    percent_high_month = 100. * max(df_close.ix[(ts + datetime.timedelta(days=int(-365/12))):(ts + datetime.timedelta(days=-1)),:]['Adj Close']) / df_close.ix[ts + datetime.timedelta(days=-1 * database_lags)]['Adj Close']
                except:
                    continue
                                        
                ev = {
                    'mean_median_diff' : mean_median_diff,
                    'p_0' : p_0,
                    'p_25' : p_25,
                    'p_50' : p_50,
                    'p_75' : p_75,
                    'p_100' : p_100,
                    'len_features_list' : len_features_list,
                    'percent_diff_lead_1_to_lead_2' : percent_diff_lead_1_to_lead_2,
                    'lag_0' : lag_0,
                    'lag_1' : lag_1,
                    'lag_2' : lag_2,
                    'lag_3' : lag_3,
                    'lag_4' : lag_4,
                    'lag_5' : lag_5,
                    'percent_high_year' : percent_high_year,
                    'percent_high_quarter' : percent_high_quarter,
                    'percent_high_month' : percent_high_month,
                    'symbol' : close,
                    'date' : date_for_reference,
                    'weekday' : weekday,
                    }
                events.append(ev)

        # save temporary results
        df_temp = pd.DataFrame(events)
        df_temp.to_csv('output/TEMP_data_for_modeling.csv', index=False)


    with open('output/events.pickle', 'w') as f:
        pickle.dump(events, f)

    df = pd.DataFrame(events)
    df.to_csv('output/data_for_modeling.csv', index=False)






                



