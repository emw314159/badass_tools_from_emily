
#
# import standard libraries
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
# import my own python tools
#
from badass_tools_from_emily.misc import weekday_map

#
# user settings
#
reorganize = False
search_database = False
match = False

user = 'neo4j'
password = 'aoeuI444'
database_lags = 2
spearmanr_lags = -100
spearman_p_cutoff = 0.1

#
# reorganize events dictionary
#
if reorganize:

    #
    # this is calculated by ../model_part_01.py
    #
    with open('/Users/emily/data/events.pickle') as f:
        events = pickle.load(f)

    #
    # iterate through the events to get a dictionary of "volume" stocks -> lists of event dates
    #
    volume_events = {}
    for e in events:
        if not volume_events.has_key(e['volume_symbol']):
            volume_events[e['volume_symbol']] = []
        volume_events[e['volume_symbol']].append(e['date'])

    #
    # save volume_events
    #
    with open('output/volume_events.pickle', 'w') as f:
        pickle.dump(volume_events, f)

else:

    #
    # load volume_events
    #
    with open('output/volume_events.pickle') as f:
        volume_events = pickle.load(f)


#
# get close for each volume (from database)
#
if search_database:

    #
    # initialize database search
    #
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
    session = driver.session()
    database_content = {}
    volume_to_close = {}
    close_to_volume = {}

    #
    # iterate through the "volume" stocks where events occurred
    #
    for volume in volume_events.keys():
        volume_to_close[volume] = {}

        #
        # find the related "close" stocks
        #
        cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY) WHERE r.lag = ' + str(database_lags) + ' AND volume.id = \'' + volume + '\' RETURN volume.id AS volume, close.id AS close, r.p_log_10 AS p_log_10;'

        result = session.run(cmd)

        for record in result:
            close = record['close']
            p_log_10 = record['p_log_10']
            volume_to_close[volume][close] = p_log_10

            if not close_to_volume.has_key(close):
                close_to_volume[close] = {}
            close_to_volume[close][volume] = p_log_10

    #
    # save "volume" stock to "close" stock relationships
    #
    with open('output/close_to_volume.pickle', 'w') as f:
        pickle.dump(close_to_volume, f)
    with open('output/volume_to_close.pickle', 'w') as f:
        pickle.dump(volume_to_close, f)


else:

    #
    # load "volume" stock to "close" stock relationships
    #
    with open('output/close_to_volume.pickle') as f:
        close_to_volume = pickle.load(f)
    with open('output/volume_to_close.pickle') as f:
        volume_to_close = pickle.load(f)

#
# match
#
if match:

    events = []

    #
    # map event dates to relevent "close" stocks
    #
    close_events = {}
    for close in close_to_volume.keys():
        for volume in close_to_volume[close].keys():
            close_events[close] = volume_events[volume]

    #
    # iterate through the "close" stocks
    #
    have_df = {}
    for close in sorted(close_events.keys()):

        print close

        #
        # load historical data for "close" stock
        #
        if not have_df.has_key(close):
            with open('../quote_data/' + close + '.pickle') as f:
                have_df[close] = pickle.load(f)
        df_close = have_df[close]

        #
        # load historical data for all related "volume" stocks
        #
        volume_list = []
        for volume in sorted(close_to_volume[close].keys()):
            if not have_df.has_key(volume):
                with open('../quote_data/' + volume + '.pickle') as f:
                    have_df[volume] = pickle.load(f)
            volume_list.append(volume)
    
        #
        # iterate through each event date for the "close" stock
        #
        for ts in close_events[close]:

            #
            # get the time series for the "close" stock for that date
            #
            close_series = df_close.ix[(ts + datetime.timedelta(days=spearmanr_lags)):(ts + datetime.timedelta(days=database_lags)),:]['Adj Close']

            #
            # iterate through the "volume" stocks associated with "close" stock
            #
            volume_feature_list = []
            for volume in volume_list:
                df_volume = have_df[volume]

                #
                # get the time series for the "volume" stock for that date
                #
                volume_series = df_volume.ix[(ts + datetime.timedelta(days=spearmanr_lags)):ts,:]['Volume']

                #
                # calculate information about that volume
                #
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

                    try:
                        last_volume_lagged = volume_lagged[-1]
                    except:
                        continue

                    volume_feature_list.append( p_log_10 * r * last_volume_lagged )

            #
            # Now we have complete analyzing the "volume" stocks related to the "close" stock.
            # Time to summarize results into an event list for modeling.
            #
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
                                        
                #
                # create event
                #
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

        #
        # save temporary results
        #
        df_temp = pd.DataFrame(events)
        df_temp.to_csv('output/TEMP_data_for_modeling.csv', index=False)

    #
    # save full results
    #
    with open('output/events.pickle', 'w') as f:
        pickle.dump(events, f)
    df = pd.DataFrame(events)
    df.to_csv('output/data_for_modeling.csv', index=False)






                



