#
# load useful libraries
#
import codecs
import pandas as pd
import os
import pprint as pp
from scipy.stats import mannwhitneyu, pearsonr
import pickle
import statsmodels.formula.api as smf
import statsmodels.api as sm
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import badass_tools_from_emily.bioinformatics.seq_utils as su
import badass_tools_from_emily.machine_learning.machine_learning as ml
from badass_tools_from_emily.misc import normalize_list_0_1

#
# user settings
#
number_of_v_fold_cycles = 1000

#
# load CRISPRs
#
df = pd.read_csv('data/df_first_WITH_SCORES.csv')

#
# write FASTQ file
#
f = open('output/query.fastq', 'w')
for seq in df['sequence']:
    f.write('@' + seq + '\n')
    f.write(seq + '\n')
    f.write('+' + '\n')
    f.write('~' * len(seq) + '\n')
f.close()

#
# find locations
#
#os.system('/rhome/emily/packages/bbmap/bbmap.sh -Xmx23g in=output/query.fastq ref=/rhome/emily/data/genomes/hg19/hg19.fasta k=9 maxindel=4 slow out=output/mapped.sam ambig=all')

#
# read mapped file
#
mapped = {}
f = open('output/mapped.sam')
for line in f:
    line = line.strip()
    if line[0] == '@':  continue
    line = [x.strip() for x in line.split('\t')]
    seq = line[0]
    chrom = line[2]
    pos = int(line[3])
    hit = line[9]

    if len(hit) == len(seq):
        if seq == hit or seq == su.rv_comp(hit):
            mapped[seq] = {'chromosome' : chrom, 'position' : pos}
f.close()

#
# reorganize mapped
#
chr_mapped = {}
for seq in mapped.keys():
    chrom = mapped[seq]['chromosome']
    pos = mapped[seq]['position']
    if not chr_mapped.has_key(chrom):
        chr_mapped[chrom] = {}
    chr_mapped[chrom][seq] = pos  # this has the effect of writing over case with two positions on one chromosome

#
# find values
#
for chrom in chr_mapped.keys():
    f = codecs.open('output/ascii_' + chrom + '.txt', encoding='ascii')
    for seq in chr_mapped[chrom].keys():
        pos = chr_mapped[chrom][seq]
        f.seek(pos)
        count = ord(f.read(1))
        mapped[seq]['count'] = count



#
# statistics
#
use = 'result_KBM7'
alt = 'result_HL60'
use_name = 'KBM-7'
alt_name = 'HL-60'
use_label = 'Log2(Fold Change, KBM-7)'
alt_label = 'Log2(Fold Change, HL-60)'

good = []
bad = []
count_list = []
for seq, y in zip(df['sequence'], df[use]):
    count_list.append(mapped[seq]['count'])
    if mapped[seq]['count'] <= 40:
        good.append(y)
    else:
        bad.append(y)
df['count'] = count_list

good_alt = []
bad_alt = []
for seq, y in zip(df['sequence'], df[alt]):
    if mapped[seq]['count'] <= 40:
        good_alt.append(y)
    else:
        bad_alt.append(y)


print
p = mannwhitneyu(good, bad)[1]
print '%0.2e' % (p)
print

print
p_alt = mannwhitneyu(good_alt, bad_alt)[1]
print '%0.2e' % (p)
print


#
# histogram of counts
#
plt.figure()
plt.hist(df['count'])
plt.savefig('output/HIST_counts.png')
plt.close()


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

