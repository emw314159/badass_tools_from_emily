#
# load useful libraries
#
import codecs
import pandas as pd
import os
import pprint as pp
from scipy.stats import mannwhitneyu, pearsonr, ttest_ind
import pickle
import statsmodels.formula.api as smf
import statsmodels.api as sm
import numpy as np
import glob
from sklearn.metrics import roc_curve, auc

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import badass_tools_from_emily.bioinformatics.seq_utils as su
import badass_tools_from_emily.machine_learning.machine_learning as ml
from badass_tools_from_emily.misc import normalize_list_0_1

#
# user settings
#
number_of_v_fold_cycles = 10
cdnas_binary = '/rhome/emily/swteam/emily/cdna/cdnas' 
cdnai_indexed_genome_directory = '/rhome/emily/data/genomes/hg19/split'

 
#
# load CRISPRs
#
df = pd.read_csv('data/df_first_WITH_SCORES.csv')

#
# write FASTA file
#
f = open('output/query.fasta', 'w')
for seq in df['sequence']:
    f.write('>' + seq + '\n')
    f.write(seq + '\n')
f.close()

# #
# # find locations
# #
# os.system('echo "" > output/locations.tsv')
# db_list = glob.glob(cdnai_indexed_genome_directory + '/*.fasta')
# for db in db_list:
#     cmd = cdnas_binary + ' -1 -E dna ' + db + ' output/query.fasta >> output/locations.tsv'
#     os.system(cmd)


#
# read locations
#
mapped = {}
f = open('output/locations.tsv')
for line in f:
    if line.strip() == '':  continue
    line = [x.strip().replace('>', '') for x in line.split('\t')]
    seq = line[0]
    chrom = line[1]
    seqpos = [int(x) for x in line[3].replace('seqpos=', '').split('..')]
    start = min(seqpos)
    end = max(seqpos)
    position = int(round(np.mean([start, end])))

    if not mapped.has_key(seq):
        mapped[seq] = {}
    if not mapped[seq].has_key(chrom):
        mapped[seq][chrom] = {}
    mapped[seq][chrom][position] = {'start' : start, 'end' : end}


#
# reorganize mapped
#
chr_mapped = {}
for seq in mapped.keys():
    for chrom in mapped[seq].keys():
        for pos in mapped[seq][chrom].keys():
            if not chr_mapped.has_key(chrom):
                chr_mapped[chrom] = {}
            if not chr_mapped[chrom].has_key(seq):
                chr_mapped[chrom][seq] = {}
            chr_mapped[chrom][seq][pos] = None

#
# find values
#
for chrom in chr_mapped.keys():
    f = codecs.open('output/ascii_' + chrom + '.txt', encoding='ascii')
    for seq in chr_mapped[chrom].keys():
        for pos in chr_mapped[chrom][seq].keys():
            f.seek(pos)
            count = ord(f.read(1))
            mapped[seq][chrom][pos]['count'] = count


#
# find median count
#
medians = {}
for seq in mapped.keys():
    count_list = []
    for chrom in mapped[seq].keys():
        for pos in mapped[seq][chrom].keys():
            count_list.append(mapped[seq][chrom][pos]['count'])
    medians[seq] = {'counts' : count_list, 'median' : np.median(count_list)}






#
# statistics
#
use = 'result_KBM7'
alt = 'result_HL60'
use_name = 'KBM-7'
alt_name = 'HL-60'
use_label = 'Log2(Fold Change, KBM-7)'
alt_label = 'Log2(Fold Change, HL-60)'
cutoff = 40




count_list = []
for seq, y in zip(df['sequence'], df[use]):
    count_list.append(medians[seq]['median'])
df['count'] = count_list


good = []
bad = []
for seq, y in zip(df['sequence'], df[use]):
    
    if medians[seq]['median'] <= cutoff:
        good.append(y)
    else:
        bad.append(y)


good_alt = []
bad_alt = []
for seq, y in zip(df['sequence'], df[alt]):
    if medians[seq]['median'] <= cutoff:
        good_alt.append(y)
    else:
        bad_alt.append(y)


print len(good), len(bad)
print len(good_alt), len(bad_alt)


print
p = mannwhitneyu(good, bad)[1]
print '%0.2e' % (p)
print

print
p_alt = mannwhitneyu(good_alt, bad_alt)[1]
print '%0.2e' % (p_alt)
print







#
# boxplot
#
plt.figure(figsize=[14, 10])
plt.subplot(1, 2, 2)
plt.boxplot([good, bad], widths=0.95)
plt.ylabel(use_label)
plt.xlabel('Chromatin Presence at gRNA Location Across Cell Lines\n(p=%0.2e, Mann-Whitney U Test)' % (p))
plt.title('Cell-Line Agnostic Impact of Chromatin Presence\nat gRNA Locations (' + use_name + ')')
plt.xticks([1, 2], ['Low (n=' + str(len(good)) + ')', 'High (n=' + str(len(bad)) + ')'])

plt.subplot(1, 2, 1)
plt.boxplot([good_alt, bad_alt], widths=0.95)
plt.ylabel(alt_label)
plt.xlabel('Chromatin Presence at gRNA Location Across Cell Lines\n(p=%0.2e, Mann-Whitney U Test)' % (p_alt))
plt.title('Cell-Line Agnostic Impact of Chromatin Presence\nat gRNA Locations (' + alt_name + ')')
plt.xticks([1, 2], ['Low (n=' + str(len(good_alt)) + ')', 'High (n=' + str(len(bad_alt)) + ')'])

plt.savefig('output/boxplot.png')
plt.close()







#
# normalize
#
df['y'] = normalize_list_0_1(df[use])

#
# negative binomial
#
formula = 'y ~ count'
y, X = ml.categorize(formula, {}, df)
model = ml.negative_binomial_wrapper(y, X)
predicted = model.predict(X)

print
print pearsonr(df['y'], predicted)
print

#
# ols
#
y, X = ml.categorize(formula, {}, df)
X['count_squared'] = [x**2. for x in X['count']]
X['count_cubed'] = [x**3. for x in X['count']]
model = ml.linear_wrapper(y, X)
predicted = model.predict(X)

print
print pearsonr(df['y'], predicted)
print

#
# cross validate
#
df['count_squared'] = [x**2. for x in df['count']] 
df['count_cubed'] = [x**3. for x in df['count']]
formula = 'y ~ count + count_squared + count_cubed'
y, X = ml.categorize(formula, {}, df)
results = ml.v_fold(ml.linear_wrapper, y, X, number_of_v_fold_cycles, verbose=True, classification=False)

sp_list = []
for sp in results['spearmanr_list']:
    if sp[1] <= 0.05:  # crude!
        sp_list.append(sp[0])



#
# histogram
#
plt.figure()
plt.hist(sp_list)
plt.savefig('output/HIST_spearmanr_OLS.png')
plt.close()

#
# ols final
#
formula = 'y ~ count + count_squared + count_cubed'
y, X = ml.categorize(formula, {}, df)
model = ml.linear_wrapper(y, X)

#
# save final model
#
with open('output/chromatin_linear_model.pickled', 'w') as f:
    pickle.dump(model, f)

#
# compare to (semi) alternate data set
#
predicted = model.predict(X)
print
print pearsonr(df[alt], predicted)
print

#
# plot regression line (semi-alternate)
#
plt.figure()
plt.plot(df[alt], predicted, '.')
x = np.arange(min(plt.xlim()), max(plt.xlim()), 0.01)
slope, intercept = np.polyfit(df[alt], predicted, 1)
abline_values = [slope * i + intercept for i in x]
plt.plot(x, abline_values, color='red')
plt.savefig('output/regression_line_OLS.png')
plt.close()

#
# ROC
#
status = []
for x in df[alt]:
    if x >= -0.8:
        status.append(1)
    else:
        status.append(0)
df['status'] = status

fpr, tpr, _ = roc_curve(df['status'], predicted)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, color='darkorange', lw=2, label='ROC Curve (Area = %0.2f)' % roc_auc)
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve for Chromatin Impact Prediction Model')
plt.legend(loc="lower right")
plt.savefig('output/ROC.png')
plt.close()

#
# try cancelling out efficiency
#

cutoff = 30


df['score'] = ((-1. * df['regression_score']) + max(df['regression_score']))
df['score'] = df['score'] / max(df['score']) 

diff = max(df[alt]) - min(df[alt])
df['score'] = df['score'] * diff
df['score'] = df['score'] + min(df[alt])    


df['corrected'] = df[alt] - df['score']


plt.figure()
plt.plot(range(0, len(df[alt])), df['corrected'], '.')
plt.savefig('output/temp.png')
plt.close()

good_alt = []
bad_alt = []
for seq, y in zip(df['sequence'], df['corrected']):
    if medians[seq]['median'] <= cutoff:
        good_alt.append(y)
    else:
        bad_alt.append(y)

print
print len(good_alt), len(bad_alt)

p = mannwhitneyu(good_alt, bad_alt)[1]
print p
p = ttest_ind(good_alt, bad_alt)[1]
print p

plt.figure()
plt.boxplot([good_alt, bad_alt], widths=0.95)
plt.xticks([1, 2], ['Low (n=' + str(len(good_alt)) + ')', 'High (n=' + str(len(bad_alt)) + ')'])
plt.savefig('output/corrected.png')
plt.close()
