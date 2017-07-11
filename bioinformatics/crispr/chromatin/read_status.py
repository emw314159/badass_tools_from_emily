#
# load useful libraries
#
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
    f = open('output/ascii_' + chrom + '.txt')
    for seq in chr_mapped[chrom].keys():
        pos = chr_mapped[chrom][seq]
        f.seek(pos)
        count = ord(f.read(1))
        mapped[seq]['count'] = count



#
# statistics
#
use = 'result_HL60'
use_label = 'Log2(Fold Change, HL60)'

good = []
bad = []
count_list = []
for seq, y in zip(df['sequence'], df[use]):
    count_list.append(mapped[seq]['count'])
    if mapped[seq]['count'] <= 20:
        good.append(y)
    else:
        bad.append(y)
df['count'] = count_list

print
p = mannwhitneyu(good, bad)[1]
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
plt.figure()
plt.boxplot([good, bad], widths=0.95)
plt.ylabel(use_label)
plt.xlabel('Chromatin Presence at gRNA Location Across Cell Lines\n(p=%0.2e, Mann-Whitney U Test)' % (p))
plt.title('Cell-Line Agnostic Impact of Chromatin Presence\nat gRNA Location')
plt.xticks([1, 2], ['Low', 'High'])
plt.savefig('output/boxplot.png')
plt.close()


#
# normalize
#
y = df[use]
y = [x - min(y) for x in y]
y = [x / max(y) for x in y]
df['y'] = y

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
# plot regression line
#
plt.figure()
plt.plot(predicted, df['y'], '.')
x = np.arange(min(plt.xlim()), max(plt.xlim()), 0.01)
slope, intercept = np.polyfit(predicted, df['y'], 1)
abline_values = [slope * i + intercept for i in x]
plt.plot(x, abline_values, color='red')
plt.savefig('output/regression_line.png')
plt.close()

#
# cross validate
#
y, X = ml.categorize(formula, {}, df)
model = ml.negative_binomial_wrapper(y, X)
print model.predict(X)
