
#
# import standard libraries
#
import pandas as pd
import pprint
import pickle
import pprint as pp
import datetime


#
# import my own python tools
#
from badass_tools_from_emily.misc import weekday_map
import badass_tools_from_emily.stock_analysis.general_model_production_functions as sa

#
# user settings
#
reorganize = False
search_database = False
match = True

output_directory = 'output'
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
    with open(output_directory + '/volume_events.pickle', 'w') as f:
        pickle.dump(volume_events, f)

else:

    #
    # load volume_events
    #
    with open(output_directory + '/volume_events.pickle') as f:
        volume_events = pickle.load(f)

#
# get close for each volume (from database)
#
if search_database:

    #
    # initialize database search
    #
    driver, session = sa.initiate_database_connection(user, password)
    database_content = {}
    volume_to_close = {}
    close_to_volume = {}

    #
    # iterate through the "volume" stocks where events occurred
    #
    for volume in volume_events.keys():
        sa.find_volume_info_in_database(volume, volume_to_close, close_to_volume, database_lags, session, driver)
        
    #
    # save "volume" stock to "close" stock relationships
    #
    with open(output_directory + '/close_to_volume.pickle', 'w') as f:
        pickle.dump(close_to_volume, f)
    with open(output_directory + '/volume_to_close.pickle', 'w') as f:
        pickle.dump(volume_to_close, f)


else:

    #
    # load "volume" stock to "close" stock relationships
    #
    with open(output_directory + '/close_to_volume.pickle') as f:
        close_to_volume = pickle.load(f)
    with open(output_directory + '/volume_to_close.pickle') as f:
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

            # TEMP NOTE:  In practice, "ts" will be yesterday and we won't pull two days ahead

            #
            # get our y value
            #
            try:
                close_series_y = df_close.ix[(ts + datetime.timedelta(days=spearmanr_lags)):(ts + datetime.timedelta(days=database_lags)),:]['Adj Close']
                percent_diff_lead_1_to_lead_2 = 100. * (close_series_y[-1] - close_series_y[-2]) / close_series_y[-2]
                close_series_diff_y = [100. * (j - i) / (i + 1.) for i, j in zip(close_series_y[0:-1], close_series_y[1:])]
                close_lagged = close_series_diff_y[database_lags:]
            except:
                continue

            #
            # iterate through the "volume" stocks associated with "close" stock
            #
            volume_feature_list = []
            for volume in volume_list:
                df_volume = have_df[volume]
                volume_series = df_volume.ix[(ts + datetime.timedelta(days=spearmanr_lags)):ts,:]['Volume']

                volume_series_diff = [100. * (j - i) / (i + 1.) for i, j in zip(volume_series[0:-1], volume_series[1:])]

                
                if len(volume_series_diff) == 0:
                    continue
                else:
                    last_diff = volume_series_diff[-1]

                if len(close_series_y) == len(volume_series) + database_lags:
                    volume_value = sa.compute_per_volume_metric(df_volume, close_to_volume, volume, close, volume_series, close_lagged, spearman_p_cutoff, last_diff)
                    if volume_value != None:
                        volume_feature_list.append(volume_value)

            #
            # Now we have complete analyzing the "volume" stocks related to the "close" stock.
            # Time to summarize results into an event list for modeling.
            #
            if len(volume_feature_list) != 0:

                # general features
                weekday = weekday_map[ts.to_pydatetime().weekday()]
                date_for_reference = str(ts.to_pydatetime().date())

                # volume list features 
                ev_volume = sa.summarize_volume_features(volume_feature_list)

                # close features
                ev_close = sa.compute_close_metrics(df_close, ts)

                #
                # create event
                #
                ev = {
                    'percent_diff_lead_1_to_lead_2' : percent_diff_lead_1_to_lead_2,
                    'symbol' : close,
                    'date' : date_for_reference,
                    'weekday' : weekday,
                    }

                for key in ev_volume.keys():
                    ev[key] = ev_volume[key]

                if ev_close != {}:
                    for key in ev_close.keys():
                        ev[key] = ev_close[key]

                    events.append(ev)

        #
        # save temporary results
        #
        df_temp = pd.DataFrame(events)
        df_temp.to_csv(output_directory + '/TEMP_data_for_modeling.csv', index=False)

    #
    # save full results
    #
    with open(output_directory + '/events.pickle', 'w') as f:
        pickle.dump(events, f)
    df = pd.DataFrame(events)
    df.to_csv(output_directory + '/data_for_modeling.csv', index=False)






                



