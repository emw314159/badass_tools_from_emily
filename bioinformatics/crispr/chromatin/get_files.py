
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
os.system('mkdir downloaded_files/combined')
os.system('mkdir downloaded_files/combined_merged')

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
# metadata
# 
bio = {}
f = open('downloaded_files/metadata.tsv')
for line in f:
    line = [x.strip() for x in line.split('\t')]
    if line[0] == 'File accession':
        continue
    filename = 'downloaded_files/' + line[0] + '.bed'
    biosample = line[6].replace(' ', '_').replace('/', '-')
    if not bio.has_key(biosample):
        bio[biosample] = []
    bio[biosample].append(filename)
f.close()



#
# join files
#
print 'Joining files...'
for biosample in sorted(bio.keys()):
    filelist = bio[biosample]
    newfile = 'downloaded_files/combined/' + biosample + '.bed'
    cmd = 'cat ' + ' '.join(filelist) + ' > ' + newfile
    os.system(cmd)

#
# sort
#
print 'Sorting files...'
filelist = glob.glob('downloaded_files/combined/*.bed')
for filename in filelist:
    coords = {}
    f = open(filename)
    for line in f:
        line = [x.strip() for x in line.split('\t')]
        chrom = line[0]
        try:
            start = int(line[1])
            end = int(line[2])
        except:
            continue
        if not coords.has_key(chrom):
            coords[chrom] = {}
        if not coords[chrom].has_key(start):
            coords[chrom][start] = {}
        coords[chrom][start][end] = None
    f.close()
    
    newfile = filename.replace('.bed', '') + '__SORTED.bed'
    f = open(newfile, 'w')
    for chrom in sorted(coords.keys()):
        for start in sorted(coords[chrom].keys()):
            for end in sorted(coords[chrom][start].keys()):
                f.write('\t'.join([chrom, str(start), str(end)]) + '\n')
    f.close()

#
# merge
#
print 'Merging files...'
filelist = glob.glob('downloaded_files/combined/*__SORTED.bed')
for filename in filelist:
    short_name = filename.split('/')[-1].replace('__SORTED.bed', '.bed')
    cmd = 'bedtools merge -i ' + filename + ' > downloaded_files/combined_merged/' + short_name
    os.system(cmd)


#
# process files
#
print 'Building counts data structure...'
counts = {}
filelist = glob.glob('downloaded_files/combined_merged/*.bed')
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
print 'Saving results...'
with open('output/counts.pickled', 'w') as f:
    pickle.dump(counts, f)
