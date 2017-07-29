
#
# import useful libraries
#
import json
import pprint as pp
import glob

#
# user settings
#
output_directory = 'output'
granger_results_directory = 'granger_computations'
quote_data_directory = 'quote_data'


#
# get symbol list
#
all_symbol_list = sorted([x.split('/')[1].replace('.pickle', '') for x in glob.glob(quote_data_directory + '/*.pickle')])

#
# write csv for all symbols
#
f = open(output_directory + '/company_nodes.csv', 'w')
f.write('id:ID,:LABEL' + '\n')
for symbol in all_symbol_list:
    f.write(','.join([symbol, 'COMPANY']) + '\n')
f.close()




#
# load data
#
close_list = sorted([x.split('/')[1].replace('.json', '') for x in glob.glob(granger_results_directory + '/*.json')])

#
# start cypher file and eliminate relationships
#
f = open('output/cypher_commands_granger_volume_adj_close.txt', 'w')
f.write('MATCH ()-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]-() DELETE r;' + '\n')

#
# start CSV file
#
f_csv = open('output/granger_volume_adj_close.csv', 'w')
f_csv.write(':START_ID,lag:int,p_log_10:float,:END_ID,:TYPE' + '\n')

#
# build cypher commands
#
for close in close_list:

    with open(granger_results_directory + '/' + close + '.json') as fp:
        pairwise = json.load(fp)

    for volume in sorted(pairwise.keys()):
        for lag in sorted(pairwise[volume].keys()):
            lag = int(lag)
            p_log_10 = pairwise[volume][str(lag)]
            cmd = 'MATCH (volume:COMPANY {id : \'' + volume + '\'}), (close:COMPANY {id : \'' + close + '\'}) CREATE (close)<-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE {lag : ' + str(lag) + ', p_log_10 : ' + str(p_log_10) + '}]-(volume) RETURN volume, close, r;'
            f.write(cmd + '\n')

            f_csv.write(','.join([volume, str(lag), str(p_log_10), close, 'VOLUME_GRANGER_CAUSES_ADJ_CLOSE']) + '\n') 
            

#
# close cypher file
#
f.close()
f_csv.close()




# ~/packages/neo4j-community-3.2.2/bin/neo4j-admin import  --database=default.graphdb --relationships output/granger_volume_adj_close.csv --nodes output/company_nodes.csv
