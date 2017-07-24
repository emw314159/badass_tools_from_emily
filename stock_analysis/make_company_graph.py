
#
# import useful libraries
#
import sys
import pandas as pd
import pprint as pp
import json

#
# urls
#
url_nyse = "http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nyse&render=download"
url_nasdaq = "http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download"
url_amex = "http://www.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=amex&render=download"
companies_by_name = 'http://www.nasdaq.com/screening/companies-by-name.aspx?render=download'

#
# user settings
#
download_companies_by_name = True
download_exchanges = True
output_directory = 'output'

#
# download companies by name
#
if download_companies_by_name:
    df = pd.DataFrame.from_csv(companies_by_name)

    #
    # remove 'Unnamed: 8'
    #
    del(df['Unnamed: 8'])

    #
    # replace 'n/a' with Python's None
    #
    for colname in list(df.columns.values):
        new_column = []
        for i in list(df[colname]):
            if i == 'n/a':
                new_column.append(None)
            else:
                new_column.append(i.strip())
        del(df[colname])
        df[colname] = new_column

    df.to_csv(output_directory + '/companies.csv', index_label='Symbol')

else:
    df = pd.read_csv(output_directory + '/companies.csv', index_col='Symbol')
    #df.index = df['Symbol']
    #del(df['Symbol'])

#
# remove whitespace from indeces
#
df.index = [x.strip() for x in list(df.index)]


#
# download exchanges
#
if download_exchanges:
    df_nyse = pd.DataFrame.from_csv(url_nyse)
    tickers_nyse = df_nyse.index.tolist()
    df_nasdaq = pd.DataFrame.from_csv(url_nasdaq)
    tickers_nasdaq = df_nasdaq.index.tolist()
    df_amex = pd.DataFrame.from_csv(url_amex)
    tickers_amex = df_amex.index.tolist()

    exchanges = {
        'nyse' : [x.strip() for x in tickers_nyse],
        'nasdaq' : [x.strip() for x in tickers_nasdaq],
        'amex' : [x.strip() for x in tickers_amex],
    }

    with open(output_directory + '/exchanges.json', 'w') as f:
        json.dump(exchanges, f)

else:
    with open(output_directory + '/exchanges.json') as f:
        exchanges = json.load(f)

        
#
# map symbol to name
#
symbol_to_name = {}
for symbol, name in zip(df.index, df['Name']):
    if not symbol_to_name.has_key(symbol):
        symbol_to_name[symbol] = {}
    symbol_to_name[symbol][name] = None

with open(output_directory + '/symbol_to_name.json', 'w') as f:
    json.dump(symbol_to_name, f)



#
# see if stock tickers overlap
#
symbols = {}
for exchange in exchanges.keys():
    for ticker in exchanges[exchange]:
        if not symbols.has_key(ticker):
            symbols[ticker] = []
        symbols[ticker].append(exchange)

print
print 'The following symbols are traded on more than one exchange:'
print
for ticker in sorted(symbols.keys()):
    if len(symbols[ticker]) != 1:
        print '\t', ticker, symbols[ticker]
        for name in sorted(symbol_to_name[ticker].keys()):
            print '\t\t', name
        print
print

#
# find unique values
#
unique_exchanges = sorted(exchanges.keys())

unique_IPOyear = {}
for iy in df['IPOyear']:
    if iy != None:
        unique_IPOyear[iy] = None

unique_Sector = {}
for s in df['Sector']:
    if s != None:
        unique_Sector[s] = None

unique_Industry = {}
for i in df['industry']:
    if i != None:
        unique_Industry[i] = None

#
# prepare MarketCap
#
new_market_cap = []
for mc in df['MarketCap']:
    value = None
    if mc != None:    
        mc = mc.replace('$', '')

        if mc[-1].isalpha():
            order = mc[-1]
            value = float(mc[0:-1])
        else:
            value = float(mc)

        if order == 'B':
            value = value * 1000000000.
        elif order == 'M':
            value = value * 1000000.

    new_market_cap.append(value)

df['float_market_cap'] = new_market_cap


#
# open file for writing cypher commands
#
f = open(output_directory + '/cypher_commands.txt', 'w')

#
# write Cypher commands for exchange nodes
#
for ex in sorted(unique_exchanges):
    cmd = 'CREATE (ex:EXCHANGE {id : \'' + ex + '\'});'
    f.write(cmd + '\n')

#
# write Cypher commands for IPOyear nodes
#
for iy in sorted(unique_IPOyear.keys()):
    cmd = 'CREATE (ipo:IPO_YEAR {id : ' + str(iy) + '});'
    f.write(cmd + '\n')

#
# write Cypher commands for sector nodes
#
for s in sorted(unique_Sector.keys()):
    cmd = 'CREATE (s:SECTOR {id : \'' + s + '\'});'
    f.write(cmd + '\n')

#
# write Cypher commands for industry nodes
#
for i in sorted(unique_Industry.keys()):
    cmd = 'CREATE (i:INDUSTRY {id : \'' + i + '\'});'
    f.write(cmd + '\n')

#
# index nodes
#
f.write('CREATE INDEX ON :EXCHANGE(id);' + '\n')
f.write('CREATE INDEX ON :IPO_YEAR(id);' + '\n')
f.write('CREATE INDEX ON :SECTOR(id);' + '\n')
f.write('CREATE INDEX ON :INDUSTRY(id);' + '\n')





#
# close the Cypher commands file
#
f.close()
