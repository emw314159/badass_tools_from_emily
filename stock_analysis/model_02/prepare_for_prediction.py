
#
# import useful standard libraries
#
import datetime
import pprint as pp
import pickle
import os
import uuid
import pandas as pd

#
# import my libraries
#
import badass_tools_from_emily.stock_analysis.general_model_production_functions as sa
from badass_tools_from_emily.misc import weekday_map

#
# user settings (set at runtime)
#
volumes_that_moved = ['ACET', 'AEH', 'FCX', 'FDC', 'FDX']  # as per prior calculation
yesterday = datetime.datetime(2017, 07, 20)
user = 'neo4j'
password = 'aoeuI444'

#
# user settings (relatively permanent)
#
database_lags = 2
spearmanr_lags = -100
prediction_quotes_dir = 'output/prediction_quotes'
spearman_p_cutoff = 0.1

#
# get a unique ID for this job
#
uid = str(uuid.uuid4())

#
# query database for volume to close information
#
driver, session = sa.initiate_database_connection(user, password)

#
# find volume info in database
#
volume_to_close = {}
close_to_volume = {}
for volume in volumes_that_moved:
    sa.find_volume_info_in_database(volume, volume_to_close, close_to_volume, database_lags, session, driver)

#
# get a unique list of all stocks involved
#
all_symbols_dict = {}
for volume in volume_to_close.keys():
    all_symbols_dict[volume] = None
    for close in volume_to_close[volume].keys():
        all_symbols_dict[close] = None
all_symbols_list = sorted(all_symbols_dict.keys())

#
# Here we download all the stocks in all symbols going back a year, with yesterday as the last date.
# Put them in prediction_quotes_dir.
#
# TEMP
#
temp_dir = prediction_quotes_dir + '_' + uid
os.system('mkdir ' + temp_dir)
for symbol in all_symbols_list:
    os.system('cp ../quote_data/' + symbol + '.pickle ' + temp_dir)

#
# load all the quote dataframes
#
have_df = {}
for symbol in all_symbols_list:
    with open(temp_dir + '/' + symbol + '.pickle') as f:
        have_df[symbol] = pickle.load(f)

#
# iterate through the "close" stocks
#
events = []
for close in sorted(close_to_volume.keys()):

    # close dataframe
    df_close = have_df[close]

    #
    # need to somehow get close_lagged
    #
    close_series, close_series_partial, close_series_diff = sa.get_current_close(df_close, yesterday, spearmanr_lags, database_lags)


    #
    # iterate through volumes associated with the close
    #
    volume_feature_list = []
    for volume in sorted(close_to_volume[close].keys()):
        df_volume = have_df[volume]

        volume_series, volume_series_diff, last_diff, volume_series_partial = sa.get_current_volume(df_volume, yesterday, spearmanr_lags, database_lags)
        if last_diff == None or str(type(volume_series_partial)) == '<type \'NoneType\'>':
            continue

        if len(close_series_partial) == len(volume_series_partial):

            volume_value = sa.compute_per_volume_metric(df_volume, close_to_volume, volume, close, volume_series_partial, close_series_diff, spearman_p_cutoff, last_diff)
            if volume_value != None:
                volume_feature_list.append(volume_value)

    #
    # record a data point if it exists
    #
    if len(volume_feature_list) != 0:
        
        # general features
        weekday = weekday_map[yesterday.weekday()]
        date_for_reference = str(yesterday.date())

        # volume list features
        ev_volume = sa.summarize_volume_features(volume_feature_list)

        # close list features
        ev_close = sa.compute_close_metrics(df_close, yesterday)

        #
        # create event
        #
        if ev_close != {} and ev_volume != {}:

            ev = {
                'symbol' : close,
                'date' : date_for_reference,
                'weekday' : weekday,
                }

            for key in ev_volume.keys():
                ev[key] = ev_volume[key]
            for key in ev_close.keys():
                ev[key] = ev_close[key]

            events.append(ev)

#
# write events to temp_dir
#
df = pd.DataFrame(events)
df.to_csv(temp_dir + '/to_score.csv', index=False)

#
# TEMP
#
os.system('cp ' + temp_dir + '/to_score.csv output')

#
# remove our temporary directory
#
os.system('rm -R ' + temp_dir)




