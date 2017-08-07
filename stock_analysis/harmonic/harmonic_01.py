

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

#
# user settings
#
symbol = 'AMZN'
quote_directory = '/Users/emily/data/quote_data'
start = datetime.datetime(2007, 1, 1)
end = datetime.datetime(2007, 12, 31)
plot_directory = '/Users/emily/Desktop/stocks'
order = 10

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
permutations = []
test = itertools.permutations(peaks_and_valleys_idx, 5)
for t in test:
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
# plot time series
#
plt.figure(figsize=[14, 10])
plt.plot(ts_narrow.index, list(ts_narrow))
plt.plot(peaks_and_valleys_dates, peaks_and_valleys_values, '.', color='green', ms=20)
plt.savefig(plot_directory + '/ts_harmonic.png')
plt.close()


