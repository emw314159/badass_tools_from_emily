#
# import useful libraries
#
import json
import pickle

import markov as mv
import shannon
import vienna
import seq_utils as su

import badass_tools_from_emily.machine_learning.machine_learning as ml


#
# prepare data
#
# example config:
#
# config = {
#     'markov_model_file' : 'output/markov_model.json',
#     'markov_model_seed_file' : 'output/markov_model_seed.json',
#     'RNAfold_binary' : '/home/emily/packages/ViennaRNA-2.3.5/src/bin/RNAfold',
# }
#
def prepare_to_score(df, seq_col_name, config):

    #
    # uppercase the sequences
    #
    df[seq_col_name] = [x.upper() for x in df[seq_col_name]]

    print
    print 'There are ' + str(len(df[seq_col_name])) + ' sequences in the data set.'


    #
    # check lengths (should all be 23)
    #
    length_dict = {}
    for seq in df[seq_col_name]:
        if not length_dict.has_key(len(seq)):
            length_dict[len(seq)] = 0
        length_dict[len(seq)] += 1

    print
    print 'Length distribution:'
    for L in sorted(length_dict.keys()):
        print '\t' + str(length_dict[L]) + ' sequences have length ' + str(L) + '.'
    print

    #
    # split off PAM sequence
    #
    pam_list = []
    pam_first_base_list = []
    sans_pam_list = []
    for seq in df[seq_col_name]:
        pam = seq[-3:]
        seq_sans_pam = seq[0:-3]
        pam_list.append(pam)
        pam_first_base_list.append(pam[0])
        sans_pam_list.append(seq_sans_pam)
    df['pam'] = pam_list
    df['pam_first_base'] = pam_first_base_list
    df['sequence_sans_pam'] = sans_pam_list

    #
    # calculate additional sequence features
    #
    data = {}
    for spacer, temp_pam in zip(df['sequence_sans_pam'], df['pam']):

        data[spacer] = {}

        # bases
        data[spacer]['base_01_from_PAM'] = spacer[-1:]
        data[spacer]['base_02_from_PAM'] = spacer[-2:-1]
        data[spacer]['base_03_from_PAM'] = spacer[-3:-2]
        data[spacer]['base_04_from_PAM'] = spacer[-4:-3]
        data[spacer]['base_05_from_PAM'] = spacer[-5:-4]
        data[spacer]['base_06_from_PAM'] = spacer[-6:-5]
        data[spacer]['base_07_from_PAM'] = spacer[-7:-6]
        data[spacer]['base_08_from_PAM'] = spacer[-8:-7]
        data[spacer]['base_09_from_PAM'] = spacer[-9:-8]
        data[spacer]['base_10_from_PAM'] = spacer[-10:-9]
        data[spacer]['base_11_from_PAM'] = spacer[-11:-10]
        data[spacer]['base_12_from_PAM'] = spacer[-12:-11]
        data[spacer]['base_13_from_PAM'] = spacer[-13:-12]
        data[spacer]['base_14_from_PAM'] = spacer[-14:-13]
        data[spacer]['base_15_from_PAM'] = spacer[-15:-14]
        data[spacer]['base_16_from_PAM'] = spacer[-16:-15]
        data[spacer]['base_17_from_PAM'] = spacer[-17:-16]
        data[spacer]['base_18_from_PAM'] = spacer[-18:-17]
        data[spacer]['base_19_from_PAM'] = spacer[-19:-18]
        data[spacer]['base_20_from_PAM'] = spacer[-20:-19]

        # complexity
        full_se = shannon.compute_shannon_entropy(spacer);  data[spacer]['se_full'] = full_se
        seed_se = shannon.compute_shannon_entropy(spacer[-3:]);  data[spacer]['se_seed_3'] = seed_se
        seed_se = shannon.compute_shannon_entropy(spacer[-4:]);  data[spacer]['se_seed_4'] = seed_se
        seed_se = shannon.compute_shannon_entropy(spacer[-5:]);  data[spacer]['se_seed_5'] = seed_se
        seed_se = shannon.compute_shannon_entropy(spacer[-6:]);  data[spacer]['se_seed_6'] = seed_se

        # binding energy
        full_be = su.calc_be(spacer);  data[spacer]['be_full'] = full_be
        seed_be = su.calc_be(spacer[-3:]);  data[spacer]['be_seed_3'] = seed_be
        seed_be = su.calc_be(spacer[-4:]);  data[spacer]['be_seed_4'] = seed_be
        seed_be = su.calc_be(spacer[-5:]);  data[spacer]['be_seed_5'] = seed_be
        seed_be = su.calc_be(spacer[-6:]);  data[spacer]['be_seed_6'] = seed_be

        # GC
        full_gc = su.calc_gc(spacer);  data[spacer]['gc_full'] = full_gc
        dist_gc = su.calc_gc(spacer[0:5]);  data[spacer]['gc_dist'] = full_gc
        seed_gc = su.calc_gc(spacer[-3:]);  data[spacer]['gc_seed_2'] = seed_gc
        seed_gc = su.calc_gc(spacer[-3:]);  data[spacer]['gc_seed_3'] = seed_gc
        seed_gc = su.calc_gc(spacer[-4:]);  data[spacer]['gc_seed_4'] = seed_gc
        seed_gc = su.calc_gc(spacer[-5:]);  data[spacer]['gc_seed_5'] = seed_gc
        seed_gc = su.calc_gc(spacer[-6:]);  data[spacer]['gc_seed_6'] = seed_gc


    #
    # reorganize and add to data frame
    #
    extra_features = {}
    for seq in df['sequence_sans_pam']:
        for key in data[seq].keys():
            if not extra_features.has_key(key):
                extra_features[key] = []
            extra_features[key].append(data[seq][key])

    for key in extra_features.keys():
        df[key] = extra_features[key]

    #
    # RNAfold
    #
    to_rnafold = {}
    for seq in df['sequence_sans_pam']:
        to_rnafold[seq] = su.rv_comp(seq).replace('T', 'U')

    from_rnafold = vienna.run_RNAfold_basic(to_rnafold, config['RNAfold_binary'])

    add_to_df = []
    for seq in df['sequence_sans_pam']:
        add_to_df.append(from_rnafold[seq]['dG'])
    df['folding_dG'] = add_to_df


    #
    # load motif models
    #
    with open(config['markov_model_file']) as f:
        markov_model = json.load(f)
    with open(config['markov_model_seed_file']) as f:
        markov_model_seed = json.load(f)

    #
    # score motifs
    #
    df['motif_scores'] = mv.score_df(markov_model, df, 'sequence_sans_pam')
    df['motif_scores_NORM_BY_LENGTH'] = mv.score_df(markov_model, df, 'sequence_sans_pam', normalize_by_length=True)
    df['seed'] = [x[-8:] for x in df['sequence_sans_pam']]
    df['motif_scores_seed'] = mv.score_df(markov_model_seed, df, 'seed')

#
# score
#
# Assumes "df" has already been through "prepare_to_score".
#
# Example "factor_options":
#
# factor_options = {
#     'base_05_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_16_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_18_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_07_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_08_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_04_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_09_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_12_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_01_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_11_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_19_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_10_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_03_from_PAM' : ['A', 'C', 'G', 'T'],
#     'base_02_from_PAM' : ['A', 'C', 'G', 'T'],
#     'pam' : ['AGG', 'CGG', 'GGG', 'TGG'],
# }
#
# Example "formula":
#
# formula = 'y ~ C(base_05_from_PAM) + C(base_16_from_PAM) + C(base_18_from_PAM) + C(base_07_from_PAM) + C(base_08_from_PAM) + C(base_04_from_PAM) + C(base_09_from_PAM) + C(base_12_from_PAM) + C(base_01_from_PAM) + C(base_11_from_PAM) + C(base_19_from_PAM) + C(base_10_from_PAM) + C(base_03_from_PAM) + C(base_02_from_PAM) + C(pam) + be_seed_5 + be_seed_6 + se_full + se_seed_5 + folding_dG + motif_scores + motif_scores_seed'
#

def score(df, model_file, formula, factor_options, drop_intercept = False, new_model_file=None):

    with open(model_file) as f:
        model = pickle.load(f)

    if new_model_file != None:
        model.output_file = new_model_file


    df[formula.split('~')[0].strip()] = 1.
    y, X = ml.categorize(formula, factor_options, df)

    if drop_intercept:
        if 'Intercept' in list(X.columns.values):
            del X['Intercept']

    prediction =  model.predict(X)
    del df[formula.split('~')[0].strip()]
    return prediction
