
#
# import useful libraries
#
import os
import glob
import pprint as pp
import pickle

#
# make the directories
#
os.system('mkdir downloaded_files')
os.system('mkdir output')

#
# download the files
#
f = open('data/files.txt')
for line in f:
    line = line.strip()
    cmd = 'wget -P downloaded_files "' + line + '"'
    os.system(cmd)
f.close()

#
# decompress the files
#
os.system('gunzip downloaded_files/*.gz')

#
# process files
#
counts = {}
filelist = glob.glob('downloaded_files/*.bed')
for filename in filelist:
    f = open(filename)
    for line in f:
        line = [x.strip() for x in line.split('\t')]
        chrom = line[0]
        start = int(line[1])
        end = int(line[2])

        if not counts.has_key(chrom):
            counts[chrom] = {}
        if not counts[chrom].has_key(start):
            counts[chrom][start] = {}
        if not counts[chrom][start].has_key(end):
            counts[chrom][start][end] = 0
        counts[chrom][start][end] += 1
    f.close()


#
# save counts
#
with open('output/counts.pickled', 'w') as f:
    pickle.dump(counts, f)
