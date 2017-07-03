
#
# useful libraries
#
import os
import random
from scipy.stats import spearmanr
from numpy import mean, arange

#
# user settings
#
random.seed(344352)

svmtrain_binary = '../packages/libsvm-3.22/svm-train'
svmpredict_binary = '../packages/libsvm-3.22/svm-predict'
scaled_data = 'SVM_REGRESSION_full.scaled'

log2c_min = -5
log2c_max = 15
log2c_step = 1

log2g_min = -15
log2g_max = 5
log2g_step = 1

log2e_min = -15
log2e_max = 10
log2e_step = 1

n_vfold = 5




#
# load full data
#
full_set = []
f = open(scaled_data)
for line in f:
    line = line.strip()
    full_set.append(line)
f.close()

N = len(full_set)

#
# iterate
#
max_sp = -2.
best_log2c = None
best_log2g = None
best_log2e = None
for log2c in list(arange(log2c_min, log2c_max + log2c_step, log2c_step)):
    for log2g in list(arange(log2g_min, log2g_max + log2g_step, log2g_step)):
        for log2e in list(arange(log2e_min, log2e_max + log2e_step, log2e_step)):

            sp_list = []
            for v in range(0, n_vfold):
                
                training_idx = random.sample( range(0, N), int(round(4. * float(N) / 5.)))
                training_idx_dict = {}
                for x in training_idx:
                    training_idx_dict[x] = None
                
                f_train = open('train.txt', 'w')
                f_test = open('test.txt', 'w')
                y_known = []

                for i, line in enumerate(full_set):
                    if training_idx_dict.has_key(i):
                        f_train.write(line + '\n')
                    else:
                        y_known.append(float(line.split(' ')[0]))
                        line = '1.0 ' + ' '.join(line.split(' ')[1:])
                        f_test.write(line + '\n')


                f_train.close()
                f_test.close()

                c = 2.**float(log2c)
                g = 2.**float(log2g)
                e = 2.**float(log2e)




                cmd = svmtrain_binary + ' -h 1 -s 3 -c ' + str(c) + ' -g ' + str(g) + ' -p ' + str(e) + ' train.txt model.txt > /dev/null 2> /dev/null'
                os.system(cmd)

                cmd = svmpredict_binary + ' test.txt model.txt prediction.txt'
                os.system(cmd)

                y_predicted = []
                f = open('prediction.txt')
                for line in f:
                    line = line.strip()
                    line = float(line)
                    y_predicted.append(line)
                f.close()

                sp = spearmanr(y_predicted, y_known)[0]
                sp_list.append(sp)

            if mean(sp_list) > max_sp:
                max_sp = mean(sp_list)
                best_log2c = log2c
                best_log2g = log2g
                best_log2e = log2e
                
            print
            print log2c, log2g, log2e
            print 'Spearman\'s R: ', max_sp
            print 'Best log2c: ', best_log2c
            print 'Best log2g: ', best_log2g
            print 'Best log2e: ', best_log2e
            print





print
print max_sp
print best_log2c
print best_log2g
print best_log2e
print       
