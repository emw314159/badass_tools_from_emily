
#
# import useful libraries
#
from subprocess import Popen, PIPE, STDOUT


#
# process program output having the three-line format (used internally)
#
def three_lines(binary, lines):
    p = Popen([binary, '--noPS', '--noconv'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)    

    stdout = p.communicate(input=lines)[0]
    output = ''
    for char in stdout.decode():
        output += char
    
    output = [x.strip() for x in output.split('\n') if x.strip() != '']

    results = {}
    for i, line in enumerate(output):
        line = line.strip()
        if i % 3 == 0:
            current_seq = line[1:] 
            results[current_seq] = {}
        if i % 3 == 1:
            results[current_seq]['sequence'] = line
        if i % 3 == 2:
            parse_list = line.split(' ')
            results[current_seq]['alignment'] = parse_list[0]
            dG = float(parse_list[-1].replace(')', '').replace('(', ''))
            results[current_seq]['dG'] = dG

    return results        




#
# Runs just the basic RNAfold (no extra calculations)
# Does not produce postscript or replace T's with U's (allegedly)
#
# Receives a dictionary of the form:
#
# {'1': 'AAAAAAATTTTTTT', '2': 'CCCCCCCGGGGGGG'}
#
# And returns a dictionary of the form:
#
# {u'1': {'dG': 0.0,
#         'folding_alignment': u'..............',
#         'sequence': u'AAAAAAATTTTTTT'},
#  u'2': {'dG': -9.1,
#         'folding_alignment': u'(((((...))))).',
#         'sequence': u'CCCCCCCGGGGGGG'}}
#
def run_RNAfold_basic(sequence_dict, binary):
    lines = []
    for key in sorted(sequence_dict.keys()):
        lines.append('>' + key)
        lines.append(sequence_dict[key])
    lines = '\n'.join(lines)
    return three_lines(binary, lines)


#
# Runs just the basic RNAcofold (no extra calculations)
# Does not produce postscript or replace T's with U's (allegedly)
#
# Receives a dictionary of the form:
#
# {
#     '1' : {
#         'seq1' : 'AAAAAAAGGGGGGG',
#         'seq2' : 'CCCCCCCTTTTTTT',
#     },
#     '2' : {
#         'seq1' : 'GAAAAAAAGGGGGGG',
#         'seq2' : 'CCCCCCCTTTTTTTC',
#     }
# }      
#
# And returns a dictionary of the form:
#
# {u'1': {'alignment': u'((((((((((((((&))))))))))))))',
#         'dG': -22.7,
#         'sequence': u'AAAAAAAGGGGGGG&CCCCCCCTTTTTTT'},
#  u'2': {'alignment': u'(((((((((((((((&)))))))))))))))',
#         'dG': -25.6,
#         'sequence': u'GAAAAAAAGGGGGGG&CCCCCCCTTTTTTTC'}}
#
def run_RNAcofold_basic(sequence_dict, binary):
    lines = []
    for key in sorted(sequence_dict.keys()):
        lines.append('>' + key)
        lines.append(sequence_dict[key]['seq1'] + '&' + sequence_dict[key]['seq2'])
    lines = '\n'.join(lines)
    return three_lines(binary, lines)



#
# demo
#
def vienna_demo():
    my_dict = {
        '1' : {
            'seq1' : 'AAAAAAAGGGGGGG',
            'seq2' : 'CCCCCCCTTTTTTT',
        },
        '2' : {
            'seq1' : 'GAAAAAAAGGGGGGG',
            'seq2' : 'CCCCCCCTTTTTTTC',
        }
    }      
    
    my_dict2 = {'1': 'AAAAAAATTTTTTT', '2': 'CCCCCCCGGGGGGG'}
    
    import pprint as pp
    stuff = run_RNAcofold_basic(my_dict, '/rhome/emily/packages/ViennaRNA-2.3.5/src/bin/RNAcofold')
    pp.pprint(stuff)
    stuff = run_RNAfold_basic(my_dict2, '/rhome/emily/packages/ViennaRNA-2.3.5/src/bin/RNAfold')
    pp.pprint(stuff)
    

