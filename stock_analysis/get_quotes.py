#
# load useful libraries
#
import pandas_datareader as pdr
from datetime import datetime
import pickle
import json

#
# user settings
#
output_directory = 'output'
quote_data_directory = 'quote_data'

#
# load symbols
#
with open(output_directory + '/symbol_to_name.json') as f:
    symbol_to_name = json.load(f)
symbol_list = sorted(symbol_to_name.keys())

#
# iterate through the symbols
#
for symbol in symbol_list:
    print symbol
    df = pdr.get_data_yahoo(symbols=symbol, start=datetime(2000, 1, 1), end=datetime(2017, 7, 25))
    with open(quote_data_directory + '/' + symbol + '.pickle', 'w') as f:
        pickle.dump(df, f)








