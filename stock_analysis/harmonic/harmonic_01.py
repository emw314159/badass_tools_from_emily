

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
# stage 1 function
#
def stage_1(args):

    t, ts_narrow, max_index_range, scan_end_point_only = args



    # check max index range
    if max(t) - min(t) > max_index_range:
        return False, t

    # check that the end is the last index, since we only want to scan for new stuff
    if scan_end_point_only:
        if list(t)[-1] != last_idx:
            return False, t

    # check that signs vary
    values = [ts_narrow[i] for i in t]
    diff = [int(np.sign(y - x)) for x, y in zip(values[0:-1], values[1:])]
    diff_test = [y != x for x, y in zip(diff[0:-1], diff[1:])]

    if not False in diff_test:
        return True, t
    else:
        return False, t

#
# main
#
if __name__ == "__main__":

    #
    # user settings
    #
    random.seed(4)
    symbol = 'AMZN'
    quote_directory = '/Users/emily/data/quote_data'
    start = datetime.datetime(2007, 1, 1)
    end = datetime.datetime(2007, 12, 31)
    plot_directory = '/Users/emily/Desktop/stocks'
    order = 10
    scan_end_point_only = False
    ratio_of_CD_to_look_ahead = 1.0
    max_index_range = int(round(365. / 2.))
    number_of_workers_in_pool = 20
    chunksize = 1000

    #
    # prepare multiprocessing
    #
    pool = Pool(processes=number_of_workers_in_pool)

    #
    # load time series
    #
    with open(quote_directory + '/' + symbol + '.pickle') as f:
        ts = pickle.load(f)['Adj Close']

    #
    # narrow down window
    #
    range_finder = [x >= start and x <= end for x in ts.index]
    #ts_narrow = ts.ix[range_finder].copy()
    ts_narrow = ts

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
    permutations = []

    print 'Permutations...'
    a = datetime.datetime.now()
    test = itertools.permutations(peaks_and_valleys_idx, 5)
    b = datetime.datetime.now()
    print b - a 




    print 'Stage 1...'
    a = datetime.datetime.now()
    data_list = []
    for t in test:
        data = (t, ts_narrow, max_index_range, scan_end_point_only)
        data_list.append(data)

    #it = pool.apply_async(stage_1, data)
       #async_results.append(it)

    it = pool.imap_unordered(stage_1, data_list, chunksize=chunksize)


    current = it.next()
    while current:
        results = current
        result, t = results
        if result:
            permutations.append(list(t))
        try:
            current = it.next()
        except:
            break

    b = datetime.datetime.now()
    print b - a 

    print 'Stage 2...'
    a = datetime.datetime.now()
    permutations_stage_2 = []
    for p in permutations:
        if not False in [y > x for x, y in zip(p[0:-1], p[1:])]:
            permutations_stage_2.append(p)
    b = datetime.datetime.now()
    print b - a 

    print 'Stage 3...'
    a = datetime.datetime.now()
    permutations_stage_3 = []
    for p in permutations_stage_2:
        test_list = [which_list(i, first, second) for i in p]
        test = [y != x for x, y in zip(test_list[0:-1], test_list[1:])]
        if not False in test:
            permutations_stage_3.append(p)

    b = datetime.datetime.now()
    print b - a 



    #
    # compute ratios
    #
    a = datetime.datetime.now()
    with_look_ahead = []
    last_index = len(ts_narrow) - 1
    for p in permutations_stage_3:
        values = [ts_narrow[i] for i in p]
        diff = [y - x for x, y in zip(values[0:-1], values[1:])]

        nearest_ratios = [abs(retracement_ratio(A, B, C)) for A, B, C in zip(values[0:-2], values[1:-1], values[2:])]
        ratio_CD_of_XA = abs(diff[-1] / diff[0])

        time_diff_XA = p[1] - p[0]
        time_diff_AB = p[2] - p[1]
        time_diff_BC = p[3] - p[2]
        time_diff_CD = p[4] - p[3]
        time_diff_XB = p[2] - p[0]
        time_diff_BD = p[4] - p[2]
        time_diff_ratio_XA_AB = float(time_diff_XA) / float(time_diff_AB)
        time_diff_ratio_BC_CD = float(time_diff_BC) / float(time_diff_CD)
        time_diff_ratio_XB_BD = float(time_diff_XB) / float(time_diff_BD)

        look_ahead_idx = int(round(ratio_of_CD_to_look_ahead * time_diff_CD)) + p[-1]

        is_bull = int(np.sign(diff[0]) >= 1)

        if look_ahead_idx <= last_index:
            end_price = ts_narrow[p[-1]]
            look_ahead_price = ts_narrow[look_ahead_idx]
            look_ahead_date = ts_narrow.index[look_ahead_idx]
            percent_change = 100. * (look_ahead_price - end_price) / look_ahead_price

            with_look_ahead.append({
                    'is_bull' : is_bull,
                    'p' : p,
                    'look_ahead_price' : look_ahead_price,
                    'look_ahead_date' : look_ahead_date,
                    'percent_change' : percent_change,
                    'ratio_CD_of_XA' : ratio_CD_of_XA,
                    'ratio_AB_of_XA' : nearest_ratios[0],
                    'ratio_BC_of_AB' : nearest_ratios[1],
                    'ratio_CD_of_BC' : nearest_ratios[2],
                    'time_diff_ratio_XA_AB' : time_diff_ratio_XA_AB,
                    'time_diff_ratio_BC_CD' : time_diff_ratio_BC_CD,
                    'time_diff_ratio_XB_BD' : time_diff_ratio_XB_BD,
                    })
    b = datetime.datetime.now()
    print b - a 


    #
    # plot time series
    #

    #p = random.sample(permutations_stage_3, 1)[0]
    #P = permutations_stage_3[-1]
    idx = -1
    p = with_look_ahead[idx]['p']
    look_ahead_price, look_ahead_date = with_look_ahead[idx]['look_ahead_price'], with_look_ahead[idx]['look_ahead_date']

    values = [ts_narrow.values[i] for i in p]
    dates = [ts_narrow.index[i] for i in p]
    pattern_values = [values[i] for i in [0, 2, 4, 2, 1, 3]]
    pattern_dates = [dates[i] for i in [0, 2, 4, 2, 1, 3]]

    plt.figure(figsize=[14, 10])
    plt.plot(ts_narrow.index, list(ts_narrow))
    plt.plot(pattern_dates, pattern_values, color='lightgray')
    plt.plot(dates, values, color='purple')
    plt.plot(peaks_and_valleys_dates, peaks_and_valleys_values, '.', color='green', ms=20)
    plt.plot(look_ahead_date, look_ahead_price, '.', color='red', ms=20)
    plt.title('Emily\'s Harmonic Scanner\n' + symbol + ' Share Price', fontsize=18)
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.savefig(plot_directory + '/ts_harmonic.png')
    plt.close()


    #
    #
    #
    for la in with_look_ahead:
        del(la['p'])
        del(la['look_ahead_date'])
        del(la['look_ahead_price'])




    df = pd.DataFrame(with_look_ahead)
    df.to_csv('data_for_regression.csv', index=False)
