
import math
from numpy import percentile
from scipy.stats import spearmanr
import random




def tri_v_fold(y_col_name, sequence_col_name, df, v_fold_cycles, count_base=0., normalize_by_length=False):
    print 'Markov v-fold:'
    spearman_list = []
    n_rows = len(df[y_col_name])
    for i in range(0, v_fold_cycles):
        print '\tIteration ' + str(i + 1)
        training_i = random.sample(range(0, n_rows), int(round((4. * float(n_rows) / 5.))))
        training_i_dict = {}
        for t in training_i:
            training_i_dict[t] = None
        training_i = sorted(training_i_dict.keys())  # removes duplicates
        testing_i = [x for x in range(0, n_rows) if not training_i_dict.has_key(x)]

        training_df = df.iloc[training_i, :]
        testing_df = df.iloc[testing_i, :]
        y_known = testing_df[y_col_name]
        model = tri(training_df, y_col_name, sequence_col_name, count_base=count_base)
        prediction = tri_score_df(model, testing_df, sequence_col_name, normalize_by_length=normalize_by_length)

        sp, p = spearmanr(y_known, prediction)
        spearman_list.append(sp)

    return spearman_list



def tri_score_df(model, df, sequence_col_name, normalize_by_length=False):
    score_list = []
    for seq in df[sequence_col_name]:
        score = tri_score_a_sequence(model, seq, normalize_by_length=normalize_by_length)
        score_list.append(score)
    return score_list



def tri_score_a_sequence(model, seq, normalize_by_length=False):
    score = 0.
    for i in range(0, len(seq) - 2):
        tri_mer = seq[i:i+3]
        base_i = tri_mer[0:2]
        base_j = tri_mer[1:3]
        score += model[base_i][base_j]
        
    if normalize_by_length:
        score = score / float(len(seq) - 2)
    return score


def tri(df, y_col_name, sequence_col_name, cutoffs=[100./3., 200./3.], count_base=0.):
    cutoff_values = percentile(df[y_col_name], cutoffs)
    lower_group_max = cutoff_values[0]
    upper_group_min = cutoff_values[1]
    lower_df = df[df[y_col_name] <= lower_group_max]
    upper_df = df[df[y_col_name] >= upper_group_min]

    lower_sequences = lower_df[sequence_col_name]
    upper_sequences = upper_df[sequence_col_name]

    all_bases = {}
    for seq_list in zip(lower_sequences, upper_sequences):
        for seq in seq_list:
            for i, base in enumerate(seq[0:-1]):
                section = seq[i:i+2]
                all_bases[section] = None
                          

    model = {}
    for key in ['lower', 'upper', 'divided', 'log_divided']:
        model[key] = {}
        for base_i in sorted(all_bases.keys()):
            model[key][base_i] = {}
            for base_j in sorted(all_bases.keys()):
                model[key][base_i][base_j] = count_base



    for key, seq_list in zip(['lower', 'upper'], [lower_sequences, upper_sequences]):
        for seq in seq_list:
            for i in range(0, len(seq) - 2):
                tri_mer = seq[i:i+3]
                base_i = tri_mer[0:2]
                base_j = tri_mer[1:3]
                model[key][base_i][base_j] += 1

    return normalize(model, all_bases, count_base)


def build_markov_model(df, y_col_name, sequence_col_name, cutoffs=[100./3., 200./3.], count_base=0.):
    cutoff_values = percentile(df[y_col_name], cutoffs)
    lower_group_max = cutoff_values[0]
    upper_group_min = cutoff_values[1]
    lower_df = df[df[y_col_name] <= lower_group_max]
    upper_df = df[df[y_col_name] >= upper_group_min]

    lower_sequences = lower_df[sequence_col_name]
    upper_sequences = upper_df[sequence_col_name]

    all_bases = {}
    for seq_list in zip(lower_sequences, upper_sequences):
        for seq in seq_list:
            for base in seq:
                all_bases[base] = None

    model = {}
    for key in ['lower', 'upper', 'divided', 'log_divided']:
        model[key] = {}
        for base_i in sorted(all_bases.keys()):
            model[key][base_i] = {}
            for base_j in sorted(all_bases.keys()):
                model[key][base_i][base_j] = count_base

    for key, seq_list in zip(['lower', 'upper'], [lower_sequences, upper_sequences]):
        for seq in seq_list:
            for i in range(0, len(seq) - 1):
                pair = seq[i:i+2]
                base_i = pair[0]
                base_j = pair[1]
                model[key][base_i][base_j] += 1

    return normalize(model, all_bases, count_base)



def normalize(model, all_bases, count_base):    

    for key in ['lower', 'upper']:
        model[key + '_normalized'] = {}
        for base_i in sorted(all_bases.keys()):
            model[key + '_normalized'][base_i] = {}
            total = 0.
            for base_j in sorted(all_bases.keys()):
                if model[key][base_i][base_j] != count_base:
                    total += model[key][base_i][base_j]
            for base_j in sorted(all_bases.keys()):
                if model[key][base_i][base_j] != count_base:
                    model[key + '_normalized'][base_i][base_j] = model[key][base_i][base_j] / total
                else:
                    model[key + '_normalized'][base_i][base_j] = 1.


    for base_i in sorted(all_bases.keys()):
        for base_j in sorted(all_bases.keys()):
            div = model['upper_normalized'][base_i][base_j] / model['lower_normalized'][base_i][base_j]
            model['divided'][base_i][base_j] = div
            model['log_divided'][base_i][base_j] = math.log(div, 2.0)

    return model['log_divided']


def score_a_sequence(model, seq, normalize_by_length=False):
    score = 0.
    for i in range(0, len(seq) - 1):
        pair = seq[i:i+2]
        base_i = pair[0]
        base_j = pair[1]
        score += model[base_i][base_j]
    if normalize_by_length:
        score = score / float(len(seq) - 1)
    return score

def score_df(model, df, sequence_col_name, normalize_by_length=False):
    score_list = []
    for seq in df[sequence_col_name]:
        score = score_a_sequence(model, seq, normalize_by_length=normalize_by_length)
        score_list.append(score)
    return score_list



def v_fold(y_col_name, sequence_col_name, df, v_fold_cycles, count_base=0., normalize_by_length=False):
    print 'Markov v-fold:'
    spearman_list = []
    n_rows = len(df[y_col_name])
    for i in range(0, v_fold_cycles):
        print '\tIteration ' + str(i + 1)
        training_i = random.sample(range(0, n_rows), int(round((4. * float(n_rows) / 5.))))
        training_i_dict = {}
        for t in training_i:
            training_i_dict[t] = None
        training_i = sorted(training_i_dict.keys())  # removes duplicates
        testing_i = [x for x in range(0, n_rows) if not training_i_dict.has_key(x)]

        training_df = df.iloc[training_i, :]
        testing_df = df.iloc[testing_i, :]
        y_known = testing_df[y_col_name]
        model = build_markov_model(training_df, y_col_name, sequence_col_name, count_base=count_base)
        prediction = score_df(model, testing_df, sequence_col_name, normalize_by_length=normalize_by_length)

        sp, p = spearmanr(y_known, prediction)
        spearman_list.append(sp)

    return spearman_list


def model_to_HTML(model, rounding_amount):

    gradient = ['#FDD3F2', '#F6BDEB', '#F0A8E5', '#EA93DE', '#E47ED8', '#DE69D1', '#D754CB', '#D13FC4', '#CB2ABE', '#C515B7', '#BF00B1']
    fg_color_list = ['black'] * 7
    fg_color_list.extend(['white'] * 4) 


    value_list = []
    for i in sorted(model.keys()):
        for j in sorted(model.keys()):
            value_list.append(round(model[i][j], rounding_amount))
    min_value = min(value_list)
    max_value = max(value_list)
    value_range = max_value - min_value
    zeroing_value = -1. * min_value 

    html = '<table style="border-collapse : collapse;">'
    html += '<tr><th>'
    for j in sorted(model.keys()):
        html += '<th style="border: 1px solid black; padding-left: 10px; padding-right: 10px; background-color : grey;">' + j + '</th>'
    html += '</th>'
    for i in sorted(model.keys()):
        html += '<tr>'
        html += '<th style="border: 1px solid black; padding-left: 10px; padding-right: 10px; background-color : grey;">' + i + '</th>'
        for j in sorted(model.keys()):
            value = round(model[i][j], rounding_amount)
            color_idx = int(math.floor((float(value + zeroing_value) / float(value_range)) * float(len(gradient)-1)))
            bg_color = gradient[color_idx]
            color = fg_color_list[color_idx]
            html += '<td style="border: 1px solid black; padding-left: 10px; padding-right: 10px; background-color : ' + bg_color + '; color : ' + color + ';">'
            html += str(value)
            html += '</td>'
        html += '</tr>'
    html += '</table>'
    return html




def example():
    import pandas as pd
    import pprint as pp
    df = pd.read_csv('/rhome/emily/swteam/emily/machine_learning/output/matched.csv')
    model = build_markov_model(df, 'e2e', 'primer', count_base=1.)
    pp.pprint(model)

    print
    print score_a_sequence(model, 'AGTTTGUTGCTTUCGCGCGTUTG')




def test_for_bias_in_dinucleotide_score_normalization_by_length():

    # CONCLUSION
    # Mean score is independant of length, but variance decreases with length. This makes sense because in longer sequences, more individual dinucleotide scores are averaged together.

    # generate random sequences
    bases = ['A', 'C', 'G', 'T', 'U']
    n = 100000
    seq_list = []
    for i in range(0, n):
        seq = ''
        L = random.sample(range(15, 41), 1)[0]
        for r in range(0, L):
            seq += random.sample(bases, 1)[0]
        seq_list.append({'sequence' : seq})

    # load model
    import json
    with open('../machine_learning/output/full_markov_model.json') as f:
        model = json.load(f)

    # make data frame
    import pandas as pd
    df = pd.DataFrame(seq_list)

    # score
    y = score_df(model, df, 'sequence', normalize_by_length=True)
    df['y'] = y
    df['lengths'] = [len(x) for x in df['sequence']]

    # bin
    bins = {}
    for y, L in zip(df['y'], df['lengths']):
        if not bins.has_key(L):
            bins[L] = []
        bins[L].append(y)

    # plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    bin_list = sorted(bins.keys())
    boxes = [bins[x] for x in bin_list]

    plt.figure()
    plt.boxplot(boxes, widths=0.9)
    plt.xticks(range(1, len(bin_list)+1), bin_list)
    plt.ylabel('Score')
    plt.xlabel('Length')
    plt.title('Looking for Length Bias in Normalization')
    plt.savefig('output/markov_norm_bias_check.png')
    plt.close()






