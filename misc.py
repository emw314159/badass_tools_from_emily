
#
# import useful libraries
#
import math




#
# normalize a list between 0. and 1.
#
def normalize_list_0_1(y):
    y = [float(x) for x in y]
    min_y = min(y)
    y = [x - min_y for x in y]
    max_y = max(y)
    y = [x / max(y) for x in y]
    return y

#
# normalize a list between 0 and 127, return as integers
#
def normalize_list_int_0_127(y):
    y = normalize_list_0_1(y)
    y = [int(round(x * 127.)) for x in y]
    return y

#
# find duplicates in a list
# (alternatively, find unique members of a list)
#
#
# this returns a dictionary where the keys are unique list items
# and the values are the counts of those items in the list
#
# the optional list argument "items_to_skip" gives a list of 
# items to ignore during this process
#
def find_duplicates_and_unique_members_of_a_list(the_list, items_to_skip=[]):
    the_dict = {}
    for item in the_list:
        if item in items_to_skip:
            continue
        if not the_dict.has_key(item):
            the_dict[item] = 0
        the_dict[item] += 1
    return the_dict    



#
# function to sort a group of lists by indices specified by sorting a given list
#
#
# "info_dict" takes the form:
#
# info_dict = {
#     'A' : [4.2, 1.3, 2.0],
#     'B' : ['Bob', 'Susan', 'Raj'],
#     'C' : [1, 2, 3],
# }
#
# Then the command "s = sort_lists_by_rank_of_another_list(info_dict, 'A')" returns
#
# s = {
#     'A' : [1.3, 2.0, 4.2],
#     'B' : ['Susan', 'Raj', 'Bob'],
#     'C' : [2, 3, 1],
# }
#
# Basically it sorts all the lists by the "indices_key".
#
# The option boolean argument "reverse" enables a reverse sort.
#
def sort_lists_by_rank_of_another_list(info_dict, indices_key, reverse=False):

    list_to_get_indices_from = info_dict[indices_key]

    if len(list_to_get_indices_from) != 0:

        indices = [i[0] for i in sorted(enumerate(list_to_get_indices_from), key=lambda x:x[1])]

        if reverse:
            indices.reverse()

        new_info_dict = {}

        for key in info_dict.keys():
            new_list = []
            for i in indices:
                new_list.append( info_dict[key][i] )
            new_info_dict[key] = new_list
        
        return new_info_dict
    else:
        return info_dict

#
# function to convert the primary keys of a dictionary to strings (to help output to JSON)
#
# found this necessary at some point
#
def convert_first_key_to_string(my_dict):
    new_dict = {}
    for key in my_dict.keys():
        new_dict[str(key)] = my_dict[key]
    return new_dict

#
# function to divide lists into chucks
#
#
# Takes a long list and returns a list of shorter lists of size "lengths" (plus the remainder).
#
# For example:
#
# my_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
#
# chunk(my_list, 2) returns:
#
# [[1, 2], [3, 4], [5, 6], [7, 8], [9]]
#
# I've needed this for long Neo4j Cypher queries
#
def chunk(the_list, lengths):
    n = int(round(float(len(the_list)) / float(lengths)))
    floor_list = [int(math.floor(float(x) / float(lengths))) for x in range(0, len(the_list))]
    floor_dict = {}
    for i, f in enumerate(floor_list):
        if not floor_dict.has_key(f):
            floor_dict[f] = []
        floor_dict[f].append(i)
    results = []
    for f in sorted(floor_dict.keys()):
        line = []
        for i in floor_dict[f]:
            line.append(the_list[i])
        results.append(line)
    return results

