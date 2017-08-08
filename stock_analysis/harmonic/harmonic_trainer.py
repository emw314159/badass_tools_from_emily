

#
# load useful libraries
#
import pprint as pp
import pickle
import numpy as np
from scipy.signal import argrelextrema
import matplotlib.pyplot as plt
import datetime
import itertools
import random
import pandas as pd
from multiprocessing import Process, Pool
import sys



#
# retracement ratio
#
def retracement_ratio(A, B, C):
    first_diff = B - A
    second_diff = C - B
    ratio = second_diff / first_diff
    return ratio


#
# which list is an index in?
#
def which_list(idx, first, second):
    if idx in first:
        return 'F'
    if idx in second:
        return 'S'
    else:
        return None


#
# compute ratios
#
def compute_ratios(p, ts_narrow, ts_full_narrow, ratio_of_CD_to_look_ahead, last_index, D_range):

    to_return = []
    
    last_point = p[-1]

    last_point_in_series = len(ts_narrow) - 1
    last_point_in_extention = min(last_point_in_series, last_point + D_range)

    if last_point != last_point_in_series:
        for p_end in range(p[-1] + 1, last_point_in_extention + 1):

            open = ts_full_narrow.ix[p_end,:]['Open']
            close = ts_full_narrow.ix[p_end,:]['Close']
            low = ts_full_narrow.ix[p_end,:]['Low']
            high = ts_full_narrow.ix[p_end,:]['High']
            percent_diff_open_to_close = 100. * (close - open) / open
            percent_diff_low_to_high = 100. * (high - low) / low
            percent_diff_close_to_high = 100. * (high - close) / close
            

            pi = [x for x in p]
            pi.append(p_end)

            values = [ts_narrow[i] for i in pi]
            diff = [y - x for x, y in zip(values[0:-1], values[1:])]

            nearest_ratios = [abs(retracement_ratio(A, B, C)) for A, B, C in zip(values[0:-2], values[1:-1], values[2:])]
            ratio_CD_of_XA = abs(diff[-1] / diff[0])

            time_diff_XA = pi[1] - pi[0]
            time_diff_AB = pi[2] - pi[1]
            time_diff_BC = pi[3] - pi[2]
            time_diff_CD = pi[4] - pi[3]
            time_diff_XB = pi[2] - pi[0]
            time_diff_BD = pi[4] - pi[2]
            time_diff_XD = pi[4] - pi[0]
            time_diff_ratio_XA_AB = float(time_diff_XA) / float(time_diff_AB)
            time_diff_ratio_BC_CD = float(time_diff_BC) / float(time_diff_CD)
            time_diff_ratio_XB_BD = float(time_diff_XB) / float(time_diff_BD)

            is_bull = int(np.sign(diff[0]) >= 1)
            if is_bull == 0:
                is_bull = -1

            price_C = ts_narrow[pi[3]]
            price_D = ts_narrow[pi[4]]
            percent_diff_C_to_D = 100. * (price_D - price_C) / price_C


            with_look_ahead = {}
            look_ahead_idx_list = [int(round(x * time_diff_CD)) + pi[-1] for x in ratio_of_CD_to_look_ahead]
            if look_ahead_idx_list[-1] <= last_index:

                end_price = ts_narrow[pi[-1]]

                for lai, ratio_ahead in zip(look_ahead_idx_list, ratio_of_CD_to_look_ahead):
                    ratio_str = str(int(round(100. * ratio_ahead)))
                    #with_look_ahead['look_ahead_price_' + ratio_str] = ts_narrow[lai]
                    #with_look_ahead['look_ahead_date_' + ratio_str] = ts_narrow.index[lai]
                    with_look_ahead['percent_change_' + ratio_str] = 100. * (ts_narrow[lai] - end_price) / ts_narrow[lai]

                with_look_ahead['is_bull'] = is_bull
                #with_look_ahead['pi'] =  pi
                with_look_ahead['ratio_CD_of_XA'] = ratio_CD_of_XA
                with_look_ahead['ratio_AB_of_XA'] = nearest_ratios[0]
                with_look_ahead['ratio_BC_of_AB'] = nearest_ratios[1]
                with_look_ahead['ratio_CD_of_BC'] = nearest_ratios[2]
                with_look_ahead['time_diff_ratio_XA_AB'] = time_diff_ratio_XA_AB
                with_look_ahead['time_diff_ratio_BC_CD'] = time_diff_ratio_BC_CD
                with_look_ahead['time_diff_ratio_XB_BD'] = time_diff_ratio_XB_BD
                with_look_ahead['time_diff_XD'] = time_diff_XD
                with_look_ahead['percent_diff_open_to_close'] = percent_diff_open_to_close 
                with_look_ahead['percent_diff_low_to_high'] = percent_diff_low_to_high
                with_look_ahead['percent_diff_close_to_high'] = percent_diff_close_to_high
                with_look_ahead['percent_diff_C_to_D'] = percent_diff_C_to_D

            if with_look_ahead != {}:
                to_return.append(with_look_ahead)


    return to_return



#
# stage 1 function
#
def stage_1(args):

    t, ts_narrow, ts_full_narrow, max_index_range, scan_end_point_only, first, second, ratio_of_CD_to_look_ahead, last_idx, symbol, D_range = args
    dict_for_dataframe = []

    # check max index range
    if max(t) - min(t) > max_index_range:
        return False, t, dict_for_dataframe

    # check that signs vary
    values = [ts_narrow[i] for i in t]
    diff = [int(np.sign(y - x)) for x, y in zip(values[0:-1], values[1:])]
    diff_test = [y != x for x, y in zip(diff[0:-1], diff[1:])]
    if False in diff_test:
        return False, t, dict_for_dataframe

    # ensure sorted
    if False in [y > x for x, y in zip(t[0:-1], t[1:])]:
        return False, t, dict_for_dataframe
    
    # ensure oscillation
    test_list = [which_list(i, first, second) for i in t]
    test = [y != x for x, y in zip(test_list[0:-1], test_list[1:])]
    if False in test:
        return False, t, dict_for_dataframe

    # compute ratios
    dict_for_dataframe = compute_ratios(t, ts_narrow, ts_full_narrow, ratio_of_CD_to_look_ahead, last_idx, D_range)
    if dict_for_dataframe == []:
        return False, t, dict_for_dataframe

    # everything checks out
    for L in dict_for_dataframe:
        L['symbol'] = symbol
    return True, t, dict_for_dataframe

#
# main
#
if __name__ == "__main__":

    #
    # user settings
    #
    random.seed(4)
    symbol = sys.argv[1]
    quote_directory = '/Users/emily/data/quote_data'
    start = datetime.datetime(2007, 1, 1)
    end = datetime.datetime(2007, 12, 31)
    plot_directory = '/Users/emily/Desktop/stocks'
    order = 10
    scan_end_point_only = False
    ratio_of_CD_to_look_ahead = [0.1, 0.25, 0.35, 0.5, 0.75, 1.0, 1.25, 1.5]

    max_index_range = int(round(    0.8 * (365. / 2.)   )) 
    D_range = int(round(    0.4 * (365. / 2.)   )) 

    number_of_workers_in_pool = 20
    chunksize = 1000
    do_it = False
    analyze_it = True

    if do_it:

        #
        # prepare multiprocessing
        #
        pool = Pool(processes=number_of_workers_in_pool)

        #
        # load time series
        #
        with open(quote_directory + '/' + symbol + '.pickle') as f:
            ts_full = pickle.load(f)
            ts = ts_full['Adj Close']


        #
        # narrow down window
        #
        range_finder = [x >= start and x <= end for x in ts.index]
        #ts_narrow = ts.ix[range_finder].copy(); ts_full_narrow = ts_full.ix[range_finder].copy()
        ts_narrow = ts; ts_full_narrow = ts_full
        

        #
        # find relative extrema
        #
        a = datetime.datetime.now()
        peaks = argrelextrema(ts_narrow.values, np.greater, order=order)[0]
        valleys = argrelextrema(ts_narrow.values, np.less, order=order)[0]
        peaks_and_valleys_idx = []
        peaks_and_valleys_idx.extend(list(peaks))
        peaks_and_valleys_idx.extend(list(valleys))
        peaks_and_valleys_idx.sort()

        # cut ends
        peaks_and_valleys_idx = peaks_and_valleys_idx[1:-1]

        # add last point
        if scan_end_point_only:
            peaks_and_valleys_idx.append(len(ts_narrow) - 1)

        peaks_and_valleys_values = [ts_narrow.values[i] for i in peaks_and_valleys_idx]
        peaks_and_valleys_dates = [ts_narrow.index[i] for i in peaks_and_valleys_idx]

        #
        # decide where to start 
        #
        if peaks[0] < valleys[0]:
            first = peaks
            second = valleys
        else:
            first = valleys
            second = peaks

        b = datetime.datetime.now()
        print b - a 



        #
        # find candidate patterns without regard to ratios
        #

        last_idx = len(ts_narrow) - 1


        data_list = []
        data_str_dict = {}

        for i in peaks_and_valleys_idx[0:-4]:
            j_list = [x for x in peaks_and_valleys_idx if x >= i and x <= max_index_range + i]
            test = itertools.permutations(j_list, 4)
            for t in test:
                str_t = '_'.join([str(x) for x in t])
                if data_str_dict.has_key(str_t):
                    continue
                data_str_dict[str_t] = None

                data = (t, ts_narrow, ts_full_narrow, max_index_range, scan_end_point_only, first, second, ratio_of_CD_to_look_ahead, last_idx, symbol, D_range)
                data_list.append(data)




        it = pool.imap_unordered(stage_1, data_list, chunksize=chunksize)

        final = []
        permutations = []

        current = it.next()
        count = 0
        while current:
            results = current
            result, t, dict_for_dataframe = results
            if result:
                permutations.append(list(t))
                final.extend(dict_for_dataframe)

                count += 1
                if count >= 5:
                    df = pd.DataFrame(final)
                    df.to_csv('TEMP_data_for_regression_' + symbol + '.csv', index=False)
                    count = 0

            try:
                current = it.next()
            except:
                break

        df = pd.DataFrame(final)
        df.to_csv('TEMP_data_for_regression_' + symbol + '.csv', index=False)
        df.to_csv('data_for_regression_' + symbol + '.csv', index=False)


        b = datetime.datetime.now()
        print b - a 




    ##################
    #    Analysis    #
    ##################

    if analyze_it:

        #
        # load useful libraries
        #
        import badass_tools_from_emily.machine_learning.machine_learning as ml
        import statsmodels.formula.api as smf

        #
        # user settings
        #
        percent_change_to_use = 'percent_change_50'
        number_of_vfold_to_run = 10

        #
        # load data
        #
        df = pd.read_csv('data_for_regression_' + symbol + '.csv')
        df['y'] = df[percent_change_to_use]
        

        #
        # more settings
        #
        formula = 'y ~ is_bull + ratio_AB_of_XA + ratio_BC_of_AB + ratio_CD_of_BC + ratio_CD_of_XA + time_diff_XD + time_diff_ratio_BC_CD + time_diff_ratio_XA_AB + time_diff_ratio_XB_BD + percent_diff_open_to_close + percent_diff_low_to_high + percent_diff_close_to_high + percent_diff_C_to_D'

        formula += ' + pow(percent_diff_C_to_D, 2.)'
        formula += ' + ratio_AB_of_XA * ratio_BC_of_AB * ratio_CD_of_BC * ratio_CD_of_XA'
        formula += ' + time_diff_ratio_BC_CD * time_diff_ratio_XA_AB * time_diff_ratio_XB_BD * time_diff_XD'
        formula += ' + percent_diff_open_to_close * percent_diff_low_to_high * percent_diff_close_to_high * percent_diff_C_to_D'

        #formula += ' + pow(percent_diff_C_to_D, 3.)'
        #formula += ' + pow(time_diff_XD, 2.)'
        #formula += ' + is_bull * percent_diff_C_to_D'

        factor_options = {}

        #
        # basic OLS regression
        #
        results = smf.ols(formula=formula, data=df).fit()
        print
        print results.summary()
        print

#         #
#         # cross-validate
#         #
#         y, X = ml.categorize(formula, factor_options, df)
#         results = ml.v_fold(ml.linear_wrapper, y, X, number_of_vfold_to_run, classification=False)
#         pp.pprint(results)

