
#
# import useful libraries
#
import math


#
# find duplicates in a list
# (alternatively, find unique members of a list)
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
def convert_first_key_to_string(my_dict):
    new_dict = {}
    for key in my_dict.keys():
        new_dict[str(key)] = my_dict[key]
    return new_dict

#
# function to divide lists into chucks
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

#
# read cypher query output
#
def read_cypher_query_output(filename, remove_quotes=False):
    results = []
    header = []
    f = open(filename)
    for line in f:
        line = line.strip()
        if line == '':  continue
        if line[0] != '|':  continue
        line = [x.strip() for x in line.split('|') if x != '']

        if header == []:
            header = line
            continue

        if remove_quotes:
            new_line = []
            for item in line:
                if item[0] == '"' and item[-1] == '"':
                    new_line.append(item[1:-1])
                else:
                    new_line.append(item)
            line = new_line

        dict_to_append = {}
        for h, item in zip(header, line):
            dict_to_append[h] = item
        results.append(dict_to_append)

    f.close()

    return results, header
