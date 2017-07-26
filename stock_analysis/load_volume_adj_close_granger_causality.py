
#
# import useful libraries
#
import json
import pprint as pp

#
# user settings
#
output_directory = 'output'

#
# load data
#
with open(output_directory + '/pairwise_causality.json') as f:
    pairwise = json.load(f)

#
# start cypher file and eliminate relationships
#
f = open('output/cypher_commands_granger_volume_adj_close.txt', 'w')
f.write('MATCH ()-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE]-() DELETE r;' + '\n')

#
# build cypher commands
#
for close in sorted(pairwise.keys()):
    for volume in sorted(pairwise[close].keys()):
        for lag in sorted(pairwise[close][volume].keys()):
            lag = int(lag)
            p_log_10 = pairwise[close][volume][str(lag)]
            cmd = 'MATCH (volume:COMPANY {id : \'' + volume + '\'}), (close:COMPANY {id : \'' + close + '\'}) CREATE UNIQUE (volume)-[r:VOLUME_GRANGER_CAUSES_ADJ_CLOSE {lag : ' + str(lag) + ', p_log_10 : ' + str(p_log_10) + '}]-(close) RETURN volume, close, r;'
            f.write(cmd + '\n')

#
# close cypher file
#
f.close()

