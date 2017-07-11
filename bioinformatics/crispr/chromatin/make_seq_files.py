
#
# import useful libraries
#
import pprint as pp
import pickle
import codecs
##from Bio import SeqIO

#
# user settings
#
###genome_fasta = '/rhome/emily/data/genomes/hg19/hg19.fasta' 
overshoot = 100

#
# load counts
#
with open('output/counts.pickled') as f:
    counts = pickle.load(f)

#
# split the file
#
list_dict = {}
for chrom in sorted(counts.keys()):
    max_end = 0
    for start in counts[chrom].keys():
        for end in counts[chrom][start].keys():
            if end > max_end:
                max_end = end
    list_dict[chrom] = [0] * (max_end + overshoot)

#
# match
#
for chrom in sorted(counts.keys()):
    for start in counts[chrom].keys():
        for end in counts[chrom][start].keys():
            value = counts[chrom][start][end]
            for i in range(start, end):
                list_dict[chrom][i] += value

#
# figure out global normalizing factor
#
max_value = 0
for chrom in list_dict.keys():
    local_max = max(list_dict[chrom])
    if local_max > max_value:
        max_value = local_max
max_value = float(max_value)



#
# convert to ascii string
#
for chrom in sorted(list_dict.keys()):
    f = codecs.open('output/ascii_' + chrom + '.txt', 'w', encoding='ascii')
    f.write(''.join([chr(int(round((float(x) / max_value) * 127.))) for x in list_dict[chrom]]) + '\n')
    f.close()

