import sys
sys.path.insert(0, '/home/ec2-user')



def prepare_for_prediction():

    #
    # import useful standard libraries
    #
    import datetime
    import pprint as pp
    import pickle
    import os
    import pandas as pd
    import sys
    import json

    #
    # import my libraries
    #
    import badass_tools_from_emily.stock_analysis.general_model_production_functions as sa
    from badass_tools_from_emily.misc import weekday_map

    #
    # load configuration
    #
    with open(sys.argv[1]) as f:
        config = json.load(f)

    #
    # user settings
    #
    prediction_quotes_dir = config['runtime_output_directory_year']
    runtime_output_directory = config['runtime_output_directory']
    user = config['user']
    password = config['password']
    database_lags = config['database_lags']
    spearmanr_lags = config['spearmanr_lags']
    spearman_p_cutoff = config['spearman_p_cutoff']

    #
    # load end date
    #
    with open(runtime_output_directory + '/end.pickle') as f:
        yesterday = pickle.load(f)

    #
    # load list of volumes that moved yesterday
    #
    with open(runtime_output_directory + '/volumes_that_moved_yesterday.json') as f:
        volumes_that_moved = json.load(f)

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
    # load all the quote dataframes
    #
    have_df = {}
    for symbol in all_symbols_list:
        with open(prediction_quotes_dir + '/' + symbol + '.pickle') as f:
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
        close_series, close_series_partial, close_series_diff, fail = sa.get_current_close(df_close, yesterday, spearmanr_lags, database_lags)
        if fail:
            continue

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
            date_for_reference = str(yesterday)

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
    # write events
    #
    df = pd.DataFrame(events)
    df.to_csv(runtime_output_directory + '/to_score.csv', index=False)



if __name__ == '__main__':
    prepare_for_prediction()





