
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
# build cypher commands
#
for close in close_list:

    with open(granger_results_directory + '/' + close + '.json') as fp:
        pairwise = json.load(fp)

    for volume in sorted(pairwise.keys()):
        for lag in sorted(pairwise[volume].keys()):
            lag = int(lag)
            p_log_10 = pairwise[volume][str(lag)]
            cmd = 'MATCH (volume:COMPANY {id : \'' + volume + '\'}), (close:COMPANY {id : \'' + close + '\'}) CREATE UNIQUE (close)<-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE {lag : ' + str(lag) + ', p_log_10 : ' + str(p_log_10) + '}]-(volume) RETURN volume, close, r;'
            f.write(cmd + '\n')

#
# close cypher file
#
f.close()
            
