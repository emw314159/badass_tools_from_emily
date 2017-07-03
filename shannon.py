#
# load useful modules
#
from math import log
from emily_code_library import find_duplicates_and_unique_members_of_a_list
    

#
# compute Shannon's entropy for a sequence
#
def compute_shannon_entropy(seq, case_insensitive=True, characters_to_skip=[]):

    if case_insensitive:
        seq = seq.upper()
    seq_as_list = list(seq)
    base_list = find_duplicates_and_unique_members_of_a_list(seq_as_list, items_to_skip=characters_to_skip).keys()

    se = 0.

    for base in base_list:
        count = seq_as_list.count(base)
        prob = float(count) / float(len(seq_as_list))
        se += -1 * prob * log(prob, 2.0)
    return se
