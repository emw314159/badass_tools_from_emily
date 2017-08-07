

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

#
# load time series
#
with open(quote_directory + '/' + symbol + '.pickle') as f:
    ts = pickle.load(f)['Adj Close']

#
# narrow down window
#
range_finder = [x >= start and x <= end for x in ts.index]
ts_narrow = ts.ix[range_finder].copy()

#
# find relative extrema
#
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
# find candidate patterns without regard to ratios
#
last_idx = len(ts_narrow) - 1
permutations = []
test = itertools.permutations(peaks_and_valleys_idx, 5)
for t in test:

    # check that the end is the last index, since we only want to scan for new stuff
    if scan_end_point_only:
        if list(t)[-1] != last_idx:
            continue

    # check that signs vary
    values = [ts_narrow[i] for i in t]
    diff = [int(np.sign(y - x)) for x, y in zip(values[0:-1], values[1:])]
    diff_test = [y != x for x, y in zip(diff[0:-1], diff[1:])]

    if not False in diff_test:
        permutations.append(list(t))

permutations_stage_2 = []
for p in permutations:
    if not False in [y > x for x, y in zip(p[0:-1], p[1:])]:
        permutations_stage_2.append(p)

permutations_stage_3 = []
for p in permutations_stage_2:
    test_list = [which_list(i, first, second) for i in p]
    test = [y != x for x, y in zip(test_list[0:-1], test_list[1:])]
    if not False in test:
        permutations_stage_3.append(p)


#
# retracement ratio
#
def retracement_ratio(A, B, C):
    first_diff = B - A
    second_diff = C - B
    ratio = second_diff / first_diff
    return ratio


#
# compute ratios
#
for p in permutations_stage_3:
    values = [ts_narrow[i] for i in p]
    diff = [y - x for x, y in zip(values[0:-1], values[1:])]
    nearest_ratios = [retracement_ratio(A, B, C) for A, B, C in zip(values[0:-2], values[1:-1], values[2:])]

    ratio_CD_of_XA = diff[-1] / diff[0]

    #print
    #print values
    #print diff
    #print nearest_ratios
    #print ratio_CD_of_XA



# [38.900002000000001, 36.43, 41.509997999999996, 37.049999, 73.650002000000001]
# [-2.4700020000000009, 5.0799979999999962, -4.4599989999999963, 36.600003000000001]






#
# plot time series
#

#p = random.sample(permutations_stage_3, 1)[0]
P = permutations_stage_3[-1]
values = [ts_narrow.values[i] for i in p]
dates = [ts_narrow.index[i] for i in p]
pattern_values = [values[i] for i in [0, 2, 4, 2, 1, 3]]
pattern_dates = [dates[i] for i in [0, 2, 4, 2, 1, 3]]

plt.figure(figsize=[14, 10])
plt.plot(ts_narrow.index, list(ts_narrow))
plt.plot(pattern_dates, pattern_values, color='lightgray')
plt.plot(dates, values, color='purple')
plt.plot(peaks_and_valleys_dates, peaks_and_valleys_values, '.', color='green', ms=20)
plt.title('Emily\'s Harmonic Scanner\n' + symbol + ' Share Price', fontsize=18)
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.savefig(plot_directory + '/ts_harmonic.png')
plt.close()


