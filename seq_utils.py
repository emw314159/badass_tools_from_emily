#
# find homopolymer segments
#
def find_homopolymer_segments(seq, skip=[]):
    last_base = ''
    chain = []
    current_chain = ''
    for base in seq:

        if base in skip:
            continue

        if base == last_base:
            current_chain += base
        else:
            if current_chain != '':
                chain.append(current_chain)
            current_chain = base
        last_base = base
    chain.append(current_chain)

    segment_lengths = [len(x) for x in chain]
    max_segment_length = max(segment_lengths)

    return chain, segment_lengths, max_segment_length


#
# compliment
#
def comp(seq):
    the_map = {
        'A' : 'T',
        'C' : 'G',
        'G' : 'C', 
        'T' : 'A',
        'U' : 'A',
        'N' : 'N',
        'a' : 't',
        'c' : 'g',
        'g' : 'c',
        't' : 'a',
        'u' : 'a',
        'n' : 'n',
    }
    new_seq = [the_map[x] for x in seq]
    new_seq = ''.join(new_seq)
    return new_seq


#
# reverse compliment
#
def rv_comp(seq):
    the_map = {
        'A' : 'T',
        'C' : 'G',
        'G' : 'C', 
        'T' : 'A',
        'U' : 'A',
        'N' : 'N',
        'a' : 't',
        'c' : 'g',
        'g' : 'c',
        't' : 'a',
        'u' : 'a',
        'n' : 'n',
    }
    new_seq = [the_map[x] for x in seq]
    new_seq.reverse()
    new_seq = ''.join(new_seq)
    return new_seq


#
# strict align
#
def strict_align(seq1, seq2):
    seq1 = list(seq1)
    seq2 = list(seq2)
    align = ''
    for i, j in zip(seq1, seq2):
        if i.lower() == j.lower():
            align += '|'
        else:
            align += ' '
    return align


#
# function to display alternative amplicon design as text
#
def display_alt_amplicon_design_text(fwd, rev, original_amplicon, design, breakpoint=None):
    rev_rc = rv_comp(rev)
    fwd_align = strict_align(fwd, original_amplicon[0:len(fwd)])

    rev_section = original_amplicon[ len(original_amplicon)-len(rev): ]
    rev_align = strict_align(rev_rc, rev_section)
    
    length_of_insert = len(original_amplicon) - len(rev) - len(fwd)
    spaces = ' ' * length_of_insert

    top_row = fwd + spaces + rev_rc
    second_row = fwd_align + spaces + rev_align

    if breakpoint != None:
        second_row_split = list(second_row)
        second_row_split[breakpoint - 1] = '*'
        second_row = ''.join(second_row_split)

    amplicon_align = strict_align(original_amplicon, design)

    result = ''
    result += 'Primers:            ' + top_row + '\n'
    result += '                    ' + second_row + '\n'
    result += 'Original Amplicon:  ' + original_amplicon + '\n'
    result += '                    ' + amplicon_align + '\n'
    result += 'Designed Amplicon:  ' + design
    return result

#
# function to compute gc content (Sequence)
#
def calc_gc(sequence):
    sequence = sequence.upper()
    gc_count = float(list(sequence).count('C') + list(sequence).count('c') + list(sequence).count('G') + list(sequence).count('g'))
    return gc_count / float(len(sequence))

#
# function to compute gc content (DataFrame)
#
def df_calc_gc(df, seq_col_name):
    gc_list = []
    for sequence in df[seq_col_name]: 
        gc_list.append(calc_gc(sequence))
    return gc_list

#
# function to calculate binding energy (RNA/DNA)
#
def calc_be(seq):
    seq = seq.upper()
    seq = seq.replace('T', 'U')

    # not sure of direction (but I think this is correct)
    seq = list(seq)
    seq.reverse()
    seq = ''.join(seq)

    #http://www2.imbf.ku.dk/Biokemi2/Nucleotide%20thermodynamics.pdf    
    delta_G_map = {
        'AA' : -1.0,
        'AC' : -2.1,
        'AG' : -1.8,
        'AU' : -0.9,
        'CA' : -0.9,
        'CC' : -2.1,
        'CG' : -1.7,
        'CU' : -0.9,
        'GA' : -1.3,
        'GC' : -2.7,
        'GG' : -2.9,
        'GU' : -1.1,
        'UA' : -0.6,
        'UC' : -1.5,
        'UG' : -1.6,
        'UU' : -0.2
    }
    delta_g = 3.1
    for n in range(0, len(seq)-1):
        i = seq[n]
        j = seq[n+1]
        try:
            delta_g += delta_G_map[i+j]
        except:
            delta_g += 0.
    return delta_g
