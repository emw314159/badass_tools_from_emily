#
# what this does
#
"""
Using data from "make_company_graph.py", this program extracts stock price and volume information using Yahoo!'s API. Saves the data to pickled files.
"""

#
# load useful libraries
#
import pandas_datareader as pdr
from datetime import datetime
import pickle
import json
import glob

#
# user settings
#
output_directory = 'output'
quote_data_directory = 'quote_data'
start = datetime(2000, 1, 1)
end = datetime(2017, 7, 25)

#
# load symbols
#
with open(output_directory + '/symbol_to_name.json') as f:
    symbol_to_name = json.load(f)
symbol_list = sorted(symbol_to_name.keys())


#
# figure out what we have already
#
file_list = glob.glob(quote_data_directory + '/*.pickle')
already_have = [x.split('/')[1].replace('.pickle', '') for x in file_list]

#
# figure out what we've tried already that didn't work.
#
with open(output_directory + '/tried_retrieving_unsuccessfully.json') as f:
    tried_getting = json.load(f)


#
# iterate through the symbols
#
for symbol in symbol_list:

    if symbol in already_have:
        continue
    if symbol in tried_getting:
        continue
    

    print symbol

    try:
        df = pdr.get_data_yahoo(symbols=symbol, start=start, end=end)
        with open(quote_data_directory + '/' + symbol + '.pickle', 'w') as f:
            pickle.dump(df, f)
    except:
        tried_getting.append(symbol)
        with open(output_directory + '/tried_retrieving_unsuccessfully.json', 'w') as f:
            json.dump(tried_getting, f)
        continue





