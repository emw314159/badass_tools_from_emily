#
# import useful libraries
#
import pprint as pp
import os
import pandas as pd
import pickle

#
# load data
#
f = open('data/msb201089-df4A.txt')
degradation_rate_map = {}
for line in f:
    line = line.strip()

    if line.upper().find('ERROR') >= 0: continue
    if line.upper().find('DEGRADATION') >= 0: continue
    if line.upper().find('HELA MRNA') >= 0: continue
    
    symbol = line.split('\t')[0]
    degradation_rate_hr = float(line.split('\t')[1])

    degradation_rate_map[symbol.upper()] = {'symbol' : symbol,
                                     'degradation_rate_hr' : degradation_rate_hr,
                                     }
f.close()

#
# load more data
#
f = open('data/s2.csv')
kd_list = []
rate_list = []
for line in f:

    line = line.strip()
    if line.find('Applied siRNA') >= 0:  continue

    id = line.split(',')[0]
    symbol = line.split(',')[1]
    kd = line.split(',')[2]

    if not degradation_rate_map.has_key(symbol): 
        continue

    kd_list.append(kd)
    rate_list.append(str(degradation_rate_map[symbol]['degradation_rate_hr']))
f.close()

#
# initialize informed prior
#
IP = ['-2.9'] * len(rate_list)

#
# write the model
#
f = open('output/model.bugs', 'w')
f.write("""model {
        for (i in 1:N) {
                IP[i] ~ dnorm(mu_IP, tau_IP)
                mu[i] <- IP[i] - alpha * T[i] - beta * T[i] * T[i]
                OP[i] ~ dnorm(mu[i], tau)
        }

        alpha ~ dnorm(mu_alpha, tau_alpha)
        beta ~ dnorm(mu_beta, tau_beta)

        mu_IP ~ dnorm(0, 10)
        tau_IP ~ dgamma(0.01, 0.01)

        mu_alpha ~ dunif(-100, 100)
        tau_alpha ~ dgamma(0.01, 0.01)

        mu_beta ~ dunif(-100, 100)
        tau_beta ~ dgamma(0.01, 0.01)

        tau ~ dgamma(0.01, 0.01)
}
""")
f.close()

#
# write the data
#
f = open('output/data.bugs', 'w')
f.write('list(\n')
f.write('  N = ' + str(len(rate_list)) + ',\n')
f.write('  OP = c(' + ','.join([str(x) for x in kd_list]) + '),\n')
f.write('  T = c(' + ','.join([str(x) for x in rate_list]) + ')\n')
f.write(')\n')
f.close()                  

#
# write the initial values
#
f = open('output/init_1.bugs', 'w')
f.write("""
list(
        alpha = 1,
        beta = 1,
        IP = c(""" + ','.join(IP) + """),
        mu_IP = 1,
        tau_IP = 1,
        mu_alpha = 1,
        tau_alpha = 1,
        mu_beta = 1,
        tau_beta = 1,
        tau = 1
        )
""")
f.close()


#
# write the script
#
f = open('output/script.txt', 'w')
f.write("""
modelCheck('output/model.bugs')
modelData('output/data.bugs')
modelCompile(1)
modelInits('output/init_1.bugs', 1)
modelUpdate(2000)
samplesSet('alpha')
samplesSet('beta')
samplesSet('IP')
samplesSet('mu_IP')
samplesSet('tau_IP')
samplesSet('mu_alpha')
samplesSet('tau_alpha')
samplesSet('mu_beta')
samplesSet('tau_beta')
samplesSet('tau')
modelUpdate(10000)
samplesStats('alpha')
samplesStats('beta')
samplesStats('IP')
samplesCoda('*', 'output/coda')
modelQuit()
""")
f.close()




#
# run the script
#
os.system('OpenBUGS307/bin/OpenBUGS output/script.txt > output/bugs_output.txt')



#
# load the script results and reorganize
#
posterior_estimates = []
f = open('output/bugs_output.txt')
for line in f:
    line = line.strip()

    if not line.find('IP[') >= 0: continue
    posterior_estimates.append(line.split(']')[1].strip().split(' ')[0])
f.close()

f = open('output/new_results.csv', 'w')
f.write('kd,rate,posterior\n')

for n in range(0, len(kd_list)):
    f.write(str(kd_list[n]) + ',' + str(rate_list[n]) + ',' + posterior_estimates[n] + '\n')
f.close()


#
# load and reorganize the CODA data
#
f = open('output/codaCODAindex.txt')
start = {}
for line in f:
    line = [x.strip() for x in line.split(' ')]
    start[ int(line[1]) - 1 ] = {
        'end' : int(line[2]) - 1,
        'variable' : line[0],
    }
f.close()    

chain = {}
f = open('output/codaCODAchain1.txt')
for i, line in enumerate(f):
    if start.has_key(i):
        variable = start[i]['variable']
    if not chain.has_key(variable):
        chain[variable] = []
    chain[variable].append(float(line.split(' ')[1]))
f.close()

#
# save CODA data in the form we are working with
#
with open('output/chain.pickled', 'w') as f:
    pickle.dump(chain, f)

import sys; sys.exit(0)


f = open('R.R', 'w')
f.write("""

the.data <- read.csv("new_results.csv")

png(filename="posterior_kd.png")
model.kd.posterior <- lm(posterior ~ kd, data=the.data)
R.value <- summary(model.kd.posterior)[[8]]
plot(posterior ~ kd, data=the.data, col="blue",
xlab="Log2( Measured Knockdown )",
ylab="Log2( Estimated Intrinsic potency )",
main="Correlation between measured knockdown and\n estimated intrinsic potency remains strong"
)
text(-0.1, -3, paste("R^2", "=", round(R.value, 4)))
graphics.off()

cutoff <- 0.005
png(filename="by_rate.png", width=1000, height=700)
par(mfrow=c(1,2))
plot(kd ~ rate, main="Measured siRNA knockdown vs. mRNA decay rate", data=subset(the.data, rate < cutoff), col="darkgray", ylab="log2( Measured knockdown )", xlab="mRNA decay rate (1/min)")
model.kd.rate <- lm(kd ~ rate, data=subset(the.data, rate < cutoff))
abline(model.kd.rate$coefficients, col="blue")
text(0.003, 1.0, paste("R^2", "=", round(summary(model.kd.rate)[[8]], 4)), col="darkblue", cex=1.5)
plot(posterior ~ rate, main="Estimated intrinsic siRNA potency vs. mRNA decay rate", data=subset(the.data, rate < cutoff), col="darkgray", ylab="log2( Estimated intrinsic potency )", xlab="mRNA decay rate (1/min)")
model.posterior.rate <- lm(posterior ~ rate, data=subset(the.data, rate < cutoff))
abline(model.posterior.rate$coefficients, col="blue")
text(0.003, 0.1, paste("R^2", "=", round(summary(model.posterior.rate)[[8]], 4)), col="darkblue", cex=1.5)
graphics.off()
""")
f.close()



os.system('R --no-save < R.R')
