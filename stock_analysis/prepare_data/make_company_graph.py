#
# what this does
#
"""
Using information published online by Nasdaq, this program builds the Neo4j Cypher commands necessary to build a graph database of companies, industries, etc. that I will leverage later.
"""

#
# import useful libraries
#
import sys
import pandas as pd
import pprint as pp
import json
from numpy import isnan

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
output_directory = '/home/ec2-user/data/database'


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
    symbol_to_name[symbol][name.strip()] = None

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

unique_name = {}
for n in df['Name']:
    unique_name[n] = None

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
# write commands to delete
#
f.write('MATCH (ex:EXCHANGE)-[r]-() DELETE ex, r;' + '\n')
f.write('MATCH (ipo:IPO_YEAR)-[r]-() DELETE ipo, r;' + '\n')
f.write('MATCH (s:SECTOR)-[r]-() DELETE s, r;' + '\n')
f.write('MATCH (i:INDUSTRY)-[r]-() DELETE i, r;' + '\n')
f.write('MATCH (c:COMPANY)-[r]-() DELETE c, r;' + '\n')
f.write('MATCH (c:COMPANY_NAME)-[r]-() DELETE c, r;' + '\n')
f.write('MATCH (ex:EXCHANGE) DELETE ex;' + '\n')
f.write('MATCH (ipo:IPO_YEAR) DELETE ipo;' + '\n')
f.write('MATCH (s:SECTOR) DELETE s;' + '\n')
f.write('MATCH (i:INDUSTRY) DELETE i;' + '\n')
f.write('MATCH (c:COMPANY) DELETE c;' + '\n')
f.write('MATCH (c:COMPANY_NAME) DELETE c;' + '\n')

#
# write Cypher commands for exchange nodes
#
for ex in sorted(unique_exchanges):
    cmd = 'CREATE (ex:EXCHANGE {id : \'' + ex.replace('\'', '\\\'') + '\'}) RETURN ex;'
    f.write(cmd + '\n')

#
# write Cypher commands for IPOyear nodes
#
for iy in sorted(unique_IPOyear.keys()):
    cmd = 'CREATE (ipo:IPO_YEAR {id : ' + str(iy) + '}) RETURN ipo;'
    f.write(cmd + '\n')

#
# write Cypher commands for sector nodes
#
for s in sorted(unique_Sector.keys()):
    cmd = 'CREATE (s:SECTOR {id : \'' + s.replace('\'', '\\\'') + '\'}) RETURN s;'
    f.write(cmd + '\n')

#
# write Cypher commands for industry nodes
#
for i in sorted(unique_Industry.keys()):
    cmd = 'CREATE (i:INDUSTRY {id : \'' + i.replace('\'', '\\\'') + '\'}) RETURN i;'
    f.write(cmd + '\n')

#
# write Cypher commands for company name nades
#
for n in sorted(unique_name.keys()):
    cmd = 'CREATE (n:COMPANY_NAME {id : \'' + n.replace('\'', '\\\'') + '\'}) RETURN n;'
    f.write(cmd + '\n')
    

#
# write Cypher commands for company nodes
#
for symbol, name, float_market_cap in zip(df.index, df['Name'], df['float_market_cap']):
    cmd = 'CREATE (c:COMPANY {id : \'' + symbol + '\''
    if not isnan(float_market_cap):
        cmd += ', market_cap : toFloat("' + str(float_market_cap) + '")'
    cmd += '}) RETURN c;'
    f.write(cmd + '\n')
    

#
# index nodes
#
f.write('CREATE INDEX ON :COMPANY(id);' + '\n')
f.write('CREATE INDEX ON :COMPANY_NAME(id);' + '\n')
f.write('CREATE INDEX ON :EXCHANGE(id);' + '\n')
f.write('CREATE INDEX ON :IPO_YEAR(id);' + '\n')
f.write('CREATE INDEX ON :SECTOR(id);' + '\n')
f.write('CREATE INDEX ON :INDUSTRY(id);' + '\n')


#
# add relationships
#
symbol_to_sector = {}
symbol_to_industry = {}
for symbol, ipo_year, sector, industry in zip(df.index, df['IPOyear'], df['Sector'], df['industry']):

    if ipo_year != None:
        cmd = 'MATCH (c:COMPANY {id : \'' + symbol + '\'}), (y:IPO_YEAR {id : ' + ipo_year + '}) CREATE UNIQUE (c)-[r:HAS_IPO_YEAR]-(y) RETURN c, r, y;'
        f.write(cmd + '\n')

    if sector != None:
        cmd = 'MATCH (c:COMPANY {id : \'' + symbol + '\'}), (s:SECTOR {id : \'' + sector + '\'}) CREATE UNIQUE (c)-[r:HAS_SECTOR]-(s) RETURN c, r, s;'
        f.write(cmd + '\n')
        symbol_to_sector[symbol] = sector

    if industry != None:
        cmd = 'MATCH (c:COMPANY {id : \'' + symbol + '\'}), (i:INDUSTRY {id : \'' + industry + '\'}) CREATE UNIQUE (c)-[r:HAS_INDUSTRY]-(i) RETURN c, r, i;'
        f.write(cmd + '\n')
        symbol_to_industry[symbol] = industry

#
# add exchanges
#
for ex in sorted(exchanges.keys()):
    for symbol in exchanges[ex]:
        cmd = 'MATCH (c:COMPANY {id : \'' + symbol + '\'}), (e:EXCHANGE {id : \'' + ex + '\'}) CREATE UNIQUE (c)-[r:HAS_EXCHANGE]-(e) RETURN c, r, e;'
        f.write(cmd + '\n')

#
# add symbol to name
#
for symbol, name in zip(df.index, df['Name']):
    cmd = 'MATCH (c:COMPANY {id : \'' + symbol + '\'}), (n:COMPANY_NAME {id: \'' + name + '\'}) CREATE UNIQUE (c)-[r:HAS_COMPANY_NAME]-(n) RETURN c, r, n;'
    f.write(cmd + '\n')


#
# close the Cypher commands file
#
f.close()

#
# save material
#
with open(output_directory + '/unique_Sector.json', 'w') as f:
    json.dump(unique_Sector, f)

with open(output_directory + '/unique_Industry.json', 'w') as f:
    json.dump(unique_Industry, f)

with open(output_directory + '/symbol_to_industry.json', 'w') as f:
    json.dump(symbol_to_industry, f)

with open(output_directory + '/symbol_to_sector.json', 'w') as f:
    json.dump(symbol_to_sector, f)

#
# write files for bulk loading
#
f = open(output_directory + '/sector_nodes.csv', 'w')
f.write('id:ID,:LABEL' + '\n')
for sector in sorted(unique_Sector.keys()):
    if sector == 'Miscellaneous':
        sector = 'Miscellaneous Sector'
    f.write(','.join([ '"' + sector + '"', 'SECTOR']) + '\n')
f.close()

f = open(output_directory + '/industry_nodes.csv', 'w')
f.write('id:ID,:LABEL' + '\n')
for industry in sorted(unique_Industry.keys()):
    if industry == 'Miscellaneous':
        industry = 'Miscellaneous Industry'
    f.write(','.join([ '"' + industry + '"', 'INDUSTRY']) + '\n')
f.close()

f = open(output_directory + '/sector_relationships.csv', 'w')
f.write(':START_ID,:END_ID,:TYPE' + '\n')
for symbol in sorted(symbol_to_sector.keys()):
    sector = symbol_to_sector[symbol]
    if sector == 'Miscellaneous':
        sector = 'Miscellaneous Sector'
    f.write(','.join([symbol, '"' + sector + '"', 'HAS_SECTOR']) + '\n')
f.close()

f = open(output_directory + '/industry_relationships.csv', 'w')
f.write(':START_ID,:END_ID,:TYPE' + '\n')
for symbol in sorted(symbol_to_industry.keys()):
    industry = symbol_to_industry[symbol]
    if industry == 'Miscellaneous':
        industry = 'Miscellaneous Industry'
    f.write(','.join([symbol, '"' + industry + '"', 'HAS_INDUSTRY']) + '\n')
f.close()


