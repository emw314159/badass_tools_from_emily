# import useful libraries
import numpy as np
import datetime
import random
import pickle
import networkx as nx
import itertools
import os
import math

# set seed for repeatibility
np.random.seed(1000)
random.seed(1000)

# user settings
number_of_mutations = 10000

# function to view the graph
def view_graph(symbol_list, graph_as_list, title, filename):
    DG = nx.DiGraph()
    for i in symbol_list:
        DG.add_node(i)
    for n in graph_as_list:
        i = n.split('_')[0]
        j = n.split('_')[1]
        value = int(n.split('_')[2])
        if value == 1:
            DG.add_edge(i, j)

    #import matplotlib.pyplot as plt
    #nx.draw_networkx(DG, alpha=0.2, node_color='orange')
    #plt.title(title)
    #plt.axis('off')
    #plt.show()

    nx.draw_graphviz(DG)
    nx.write_dot(DG, filename)

# load the Dow Jones Industrial Average symbols
djia = sorted(['AXP', 'BA', 'CAT', 'CVX', 'DD', 'DIS', 'GE', 'GS', 'HD', 'IBM', 'JNJ', 'JPM', 'KO', 'MCD', 'MMM', 'MRK', 'NKE', 'PFE', 'PG', 'T', 'TRV', 'UNH', 'UTX', 'V', 'VZ', 'WMT', 'XOM'])

# specify the time points we want to sample from
end_date = datetime.datetime(2014, 10, 28, 0, 0)
start_date = datetime.datetime(2013, 10, 29, 0, 0)

# load the closing prices for the given dates into memory
prices = {}
f = open('data.csv')
for line in f:
    line = line.strip()

    date_string = line.split(',')[1]
    year = int(date_string.split('-')[0])
    month = int(date_string.split('-')[1])
    day = int(date_string.split('-')[2])
    date_as_datetime = datetime.datetime(year, month, day)

    if date_as_datetime < start_date:  continue
    if date_as_datetime > end_date:  continue

    symbol = line.split(',')[0]
    if symbol not in djia:  continue
    close = float(line.split(',')[5])
    if not prices.has_key(symbol):
        prices[symbol] = {}
    prices[symbol][date_string] = close
f.close()

# convert to time series
prices_ts = {}
for symbol in prices:
    prices_ts[symbol] = []
    for d in sorted(prices[symbol].keys()):
        prices_ts[symbol].append(prices[symbol][d])

# compute percent change
percent_change = {}
for symbol in prices_ts.keys():
    ts = prices_ts[symbol]
    percent_change[symbol] = [(ts[i] - ts[i-1]) / ts[i-1] for i in range(1, len(ts))]

# discretize
p1_list = []
for i in range(0, len(percent_change[djia[0]])):
    pc_list = []
    for symbol in percent_change.keys():
        pc_list.append(percent_change[symbol][i])
    p1 = np.percentile(pc_list, 50.0)
    p1_list.append(p1)
discretized_change = {}
for symbol in percent_change.keys():
    discretized_change[symbol] = []
    for i, pc in enumerate(percent_change[symbol]):
        if pc <= p1_list[i]:
            discretized_change[symbol].append(0)
        else:
            discretized_change[symbol].append(1)
                                            
# compile an array containing a list of each stock's discretized change in price for each date
symbol_list = sorted(discretized_change.keys())
MOVEMENT_LEVELS = []
for i in range(0, len(percent_change[djia[0]])):
    movement_levels_at_time = []
    for symbol in symbol_list:
        movement_levels_at_time.append(discretized_change[symbol][i])
    MOVEMENT_LEVELS.append(movement_levels_at_time)

# see if there are duplicate movement levels and assign probability to level combination
movement_levels_dict = {}
for e in MOVEMENT_LEVELS:
    e = [str(x) for x in e]
    if not movement_levels_dict.has_key(','.join(e)):
        movement_levels_dict[','.join(e)] = 0
    movement_levels_dict[','.join(e)] += 1
prob_dict = {}
for e in movement_levels_dict.keys():
    prob_dict[e] = movement_levels_dict[e] * (1. / len(MOVEMENT_LEVELS))

# generate an initial graph
graph_as_list = []
for i in symbol_list:
    for j in symbol_list:
        if i == j:  continue
        graph_as_list.append(i + '_' + j + '_0')
view_graph(symbol_list, graph_as_list, 'Initial Bayesian Network of DJIA Stocks\' Change in Closing Prices', 'output/initial_graph.dot')


# score graph
def score_graph(G, pd):

    # used later for penalizing graphs with many connections
    direction_zero_count = 0

    # identify the parents of each child node
    parents = {}
    for node in G:
        i = node.split('_')[0]
        j = node.split('_')[1]
        direction = node.split('_')[2]
        if not parents.has_key(j):  parents[j] = []
        if direction == '0':  
            direction_zero_count += 1
            continue
        if direction == '1':  parents[j].append(i)

    # compute probabilities of each node given parent nodes
    probs = {}
    for child in sorted(parents.keys()):

        # denominator (this is the probability of the "given" side of the conditional probability)
        DENOMINATOR = {}
        sets = []
        parent_list = []
        parent_list_index = []
        for parent in sorted(parents[child]):
            parent_list.append(parent)
            parent_list_index.append(symbol_list.index(parent))
            sets.append(['0', '1'])
        cases = []
        for i in itertools.product(*sets):
            cases.append(list(i))
        for case in cases:
            denominator = 0.
            for pd1 in pd.keys():
                pd1 = pd1.split(',')
                all_match = True
                for i, pli in enumerate(parent_list_index):
                    if case[i] != pd1[pli]:
                        all_match = False
                if all_match:  denominator += pd[','.join(pd1)]
            DENOMINATOR[','.join(case)] = denominator
            
            # return from function if denominator is zero
            if denominator == 0.0:
                return -99999999999999.0, {}, {}
        
        # data structure for storing the conditional probability of each node
        probs[child] = {}

        # numerator (this is the probability of the event and the "given" side of the conditional probability
        sets = []
        all_list = []
        all_list_index = []
        all_list_symbols = [child]
        all_list_symbols.extend(sorted(parents[child]))
        for all_item in all_list_symbols:
            all_list.append(all_item)
            all_list_index.append(symbol_list.index(all_item))
            sets.append(['0', '1'])
        cases = []
        for i in itertools.product(*sets):
            cases.append(list(i))
        for case in cases:
            numerator = 0.
            for pd1 in pd.keys():
                pd1 = pd1.split(',')
                all_match = True
                for i, pli in enumerate(all_list_index):
                    if case[i] != pd1[pli]:
                        all_match = False
                if all_match:
                    numerator += pd[','.join(pd1)]
            probs[child][','.join(case)] = numerator / DENOMINATOR[','.join(case[1:])]

    # score each pd element
    BN_dict = {}
    BN_list = []
    SBN_dict = {}
    SBN_list = []
    for pds in pd.keys():
        pds = pds.split(',')
        BN = 1.
        for i in range(0, len(pds)):
            symbol = symbol_list[i]
            parent_list = sorted(parents[symbol])
            parent_indexes = [symbol_list.index(x) for x in parent_list]

            case = [pds[i]]
            case.extend([pds[x] for x in parent_indexes])
            case = ','.join(case)

            BN = BN * probs[symbol][case]

        BN_dict[','.join(pds)] = BN
        BN_list.append(BN)
        SBN_dict[','.join(pds)] = math.log10(BN)
        SBN_list.append(math.log10(BN))

    # this is the probability of the graph, used to penalize graphs with high number of edges
    graph_prob = math.log10(float(direction_zero_count) / float(len(G)))

    return sum(SBN_list) + graph_prob, BN_dict, SBN_dict


# iterate
score, BN_d, SBN_d = score_graph(graph_as_list, prob_dict)
BN_d_storage = {}
SBN_d_storage = {}
for i in range(0, number_of_mutations):

    old_graph = graph_as_list
    new_graph = [x for x in old_graph]

    # possibly activate or disactivate an edge to form a new graph
    edge = random.sample(graph_as_list, 1)[0]
    edge_index = old_graph.index(edge)
    r = random.uniform(0, 1)
    direction = '0'
    if r >= 0.5:  direction = '1'
    new_edge = edge.split('_')[0:2]
    new_edge.append(direction)
    new_graph[edge_index] = '_'.join(new_edge)

    # evaluate the new model
    test_score, BN_d, SBN_d = score_graph(new_graph, prob_dict)
    if test_score > score:
        score = test_score
        graph_as_list = new_graph
        BN_d_storage = BN_d
        SBN_d_storage = SBN_d
    else:
        graph_as_list = old_graph

    print 'Iteration:', i, '  Score:', score

# output final probabilities
f = open('output/probs.txt', 'w')
f.write('\t'.join(['movement', 'prob_dict', 'BN', 'SBN']) + '\n')
for b in sorted(BN_d_storage.keys()):
    f.write('\t'.join([b, str(prob_dict[b]), str(BN_d_storage[b]), str(SBN_d_storage[b])]) + '\n')
f.close()

# output final graph
view_graph(symbol_list, graph_as_list, 'Learned Bayesian Network of DJIA Stocks\' Change in Closing Prices', 'output/final_graph.dot')

# edit final graph
def edit_graph(filename):
    f = open(filename)
    new_graph = ''
    for line in f:
        line = line.strip()
        if line != '}':  
            new_graph += line.replace(';', ' [arrowsize=2.0];') + '\n'
    f.close()
    for symbol in symbol_list:
        new_graph += symbol + ' [color=orange, style=filled, fontsize=30];\n'
    new_graph += '}'
    f_out = open(filename + '_EDITED', 'w')
    f_out.write(new_graph + '\n')
    f_out.close()

edit_graph('output/initial_graph.dot')
edit_graph('output/final_graph.dot')

# graphviz commands
os.system('dot -Tpng output/initial_graph.dot_EDITED > output/initial_graph.png')
os.system('dot -Tpng output/final_graph.dot_EDITED > output/final_graph.png')
