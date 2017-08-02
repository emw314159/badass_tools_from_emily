#
# import useful standard libraries
#
from scipy.stats import spearmanr
from numpy import percentile, mean, isnan
from neo4j.v1 import GraphDatabase, basic_auth
import datetime

#
# initiate database connection
#
def initiate_database_connection(user, password):
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
    session = driver.session()
    return driver, session

#
# find volume info in database
#
def find_volume_info_in_database(volume, volume_to_close, close_to_volume, database_lags, session, driver):
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
# compute per volume metric
#
def compute_per_volume_metric(df_volume, close_to_volume, volume, close, volume_series, close_lagged, spearman_p_cutoff, last_diff):
    return_value = None

    p_log_10 = -1. * close_to_volume[close][volume]
    
    volume_series_diff = [100. * (j - i) / (i + 1.) for i, j in zip(volume_series[0:-1], volume_series[1:])]
    volume_lagged = volume_series_diff
    
    r, p = spearmanr(close_lagged, volume_lagged)

    if isnan(r):
        return_value = None
    else:
        if p > spearman_p_cutoff:
            r = 0.
            return_value = None
        else:
            try:
                return_value = p_log_10 * r * last_diff
            except:
                return_value = None
            
    return return_value
        
#
# summarize volume features
#
def summarize_volume_features(volume_feature_list):
    return_dict = {}
    percentile_list = percentile(volume_feature_list, [0., 25., 50., 75., 100.])
    mean_median_diff = mean(volume_feature_list) - percentile_list[2]
    p_0 = percentile_list[0]
    p_25 = percentile_list[1]
    p_50 = percentile_list[2]
    p_75 = percentile_list[3]
    p_100 = percentile_list[4]
    len_features_list = len(volume_feature_list)
    return_dict = {
        'mean_median_diff' : mean_median_diff,
        'p_0' : p_0,
        'p_25' : p_25,
        'p_50' : p_50,
        'p_75' : p_75,
        'p_100' : p_100,
        'len_features_list' : len_features_list,
        }
    return return_dict

#
# compute close metrics
#
def compute_close_metrics(df_close, ts):

    return_dict = {}

    close_series = df_close.ix[(ts + datetime.timedelta(days=-366)):ts,:]['Adj Close']
    close_series_diff = [100. * (j - i) / (i + 1.) for i, j in zip(close_series[0:-1], close_series[1:])]

    lag_0 = close_series_diff[-1]
    lag_1 = close_series_diff[-2]
    lag_2 = close_series_diff[-3]
    lag_3 = close_series_diff[-4]
    lag_4 = close_series_diff[-5]
    lag_5 = close_series_diff[-6]

    no_percent = False
    try:

        percent_high_year = 100. *  close_series.ix[ts,:] / max(close_series.ix[(ts + datetime.timedelta(days=-366)):(ts + datetime.timedelta(days=-1))])

        percent_high_quarter = 100. * close_series.ix[ts,:] / max(close_series.ix[(ts + datetime.timedelta(days=int(round(-366./4.)))):(ts + datetime.timedelta(days=-1))]) / close_series.ix[ts,:]

        percent_high_month = 100. * close_series.ix[ts,:] / max(close_series.ix[(ts + datetime.timedelta(days=int(round(-366./12.)))):(ts + datetime.timedelta(days=-1))]) / close_series.ix[ts,:]

    except:
        no_percent = True


    lag_average_dict = {}
    lag_list = [lag_0, lag_1, lag_2, lag_3, lag_4, lag_5]
    for i in range(2, len(lag_list) + 1):
        lag_average_dict['lag_average_' + str(i)] = mean(lag_list[0:i])
        
    if no_percent:
        return_dict = {}
    else:
        return_dict = {
            'lag_0' : lag_0,
            'lag_1' : lag_1,
            'lag_2' : lag_2,
            'lag_3' : lag_3,
            'lag_4' : lag_4,
            'lag_5' : lag_5,
            'percent_high_year' : percent_high_year,
            'percent_high_quarter' : percent_high_quarter,
            'percent_high_month' : percent_high_month,
            }

        for key in lag_average_dict.keys():
            return_dict[key] = lag_average_dict[key]

    return return_dict

#
# get "current" close information
#
def get_current_close(df_close, ts, spearmanr_lags, database_lags):

    fail = False
    
    try:
        close_series = df_close.ix[(ts + datetime.timedelta(days=spearmanr_lags + -1 * database_lags)):ts,:]['Adj Close']
        close_series_partial = close_series.ix[(close_series.index[database_lags]):,]
        close_series_diff = [100. * (j - i) / (i + 1.) for i, j in zip(close_series_partial[0:-1], close_series_partial[1:])]
    except:
        fail = True
        close_series = None
        close_series_partial = None
        close_series_diff = None

    return close_series, close_series_partial, close_series_diff, fail

#
# get "current" volume information
#
def get_current_volume(df_volume, ts, spearmanr_lags, database_lags):
    volume_series = df_volume.ix[(ts + datetime.timedelta(days=spearmanr_lags + -1 * database_lags)):ts,:]['Volume']
    volume_series_diff = [100. * (j - i) / (i + 1.) for i, j in zip(volume_series[0:-1], volume_series[1:])]

    if len(volume_series_diff) == 0:
        last_diff = None
    else:
        last_diff = volume_series_diff[-1]

    try:
        volume_series_partial = volume_series.ix[(volume_series.index[0]):(volume_series.index[-1 * database_lags - 1]),]
    except:
        volume_series_partial = None

    return volume_series, volume_series_diff, last_diff, volume_series_partial
