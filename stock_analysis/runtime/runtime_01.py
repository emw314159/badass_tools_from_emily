#
# load useful libraries
#
import pickle
import pprint as pp
import datetime
from neo4j.v1 import GraphDatabase, basic_auth
import pandas as pd
import json
import pandas_datareader as pdr

from badass_tools_from_emily.misc import chunk

#
# user settings
#
user = 'neo4j'
password = 'aoeuI111'
volume_threshold = 500000
database_lags = 2
runtime_output_directory = 'output'
query_database_for_movers = False
get_two_day_stocks = True


#
# connect to database
#
driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth(user, password))
session = driver.session()

#
# get volume movers known to database
#
if query_database_for_movers:
    cmd = 'MATCH (volume:COMPANY)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]->(close:COMPANY) WHERE r.lag = ' + str(database_lags) + ' RETURN volume.id AS volume, close.id AS close, r.lag as lag, r.p_log_10 as p_log_10;'
    volume_movers = {}
    result = session.run(cmd)
    for record in result:
        volume = record['volume']
        close = record['close']
        lag = str(record['lag'])
        p_log_10 = record['p_log_10']

        if not volume_movers.has_key(volume):
            volume_movers[volume] = {}
        if not volume_movers[volume].has_key(close):
            volume_movers[volume][close] = p_log_10

    with open(runtime_output_directory + '/volume_movers.json', 'w') as f:
        json.dump(volume_movers, f)

else:
    with open(runtime_output_directory + '/volume_movers.json') as f:
        volume_movers = json.load(f)




#
#
#
def f(volume_list, n, start, end, volumes_that_moved_yesterday):

    errors = []
    chunks = chunk(volume_list, n)
    
    print
    print len(chunks)
    print

    for i, c in enumerate(chunks):

        print i

        try:
            panel = pdr.get_data_yahoo(symbols=c, start=start, end=end)
            
            for symbol in c:
                df = panel.minor_xs(symbol)
                df = df.sort_index()
                d_volume = [(100. * (j - i) / i) for i, j in zip(df['Volume'][0:-1], df['Volume'][1:])]
                if d_volume[-1] >= volume_threshold:
                    volumes_that_moved_yesterday.append(symbol)
        except:
            errors.extend(c)
    
    return errors


#
# get two day stocks
#
volumes_that_moved_yesterday = []
if get_two_day_stocks:
    volume_list = sorted(volume_movers.keys())
    end = (datetime.datetime.now() + datetime.timedelta(days=-1)).date()
    start = (end + datetime.timedelta(days=-8))

    errors = f(volume_list, 200, start, end, volumes_that_moved_yesterday)

    print
    print 'length(errors) = ' + str(len(errors)) + '\t' + str(len(volumes_that_moved_yesterday))
    print

    errors = f(errors, 10, start, end, volumes_that_moved_yesterday)

    print
    print 'length(errors) = ' + str(len(errors)) + '\t' + str(len(volumes_that_moved_yesterday))
    print


    with open(runtime_output_directory + '/volumes_that_moved_yesterday.json', 'w') as f:
        json.dump(volumes_that_moved_yesterday, f)

else:
    with open(runtime_output_directory + '/volumes_that_moved_yesterday.json') as f:
        volumes_that_moved_yesterday = json.load(f)




