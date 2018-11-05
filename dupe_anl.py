import os
from scipy import spatial

def dic_cos(d1, d2):
    for key in d1:
        if key not in d2:
            d2[key] = 0
    for key in d2:
        if key not in d1:
            d1[key] = 0

    hashes = sorted(d1.keys())
    list1 =[]
    list2 =[]
    for hash in hashes:
        list1.append(d1[hash])
        list2.append(d2[hash])
    return spatial.distance.cosine(list1, list2)


base = "/home/nick/Development/crawl_data/"

folders = os.listdir(base)

topics = ['camping', 'golf','women fashion']
n = 3

groupcounts = {}
topiccounts = {}
for t in topics:
    topiccounts[t] = {}
    for i in range(n):
        groupcounts[t+'_'+str(i)] = {}
        dir = base + t + '_' + str(i) + '/hashgroups/'
        hashgroups = os.listdir(dir)
        for group in hashgroups:
            groupcounts[t+'_'+str(i)][group] = len(os.listdir(dir+group))
            if group in topiccounts[t]:
                topiccounts[t][group] += len(os.listdir(dir+group))
            else:
                topiccounts[t][group] = len(os.listdir(dir+group))

for k in range(len(topics)):
    t = topics[k]
    intradiff = 0
    for i in range(n):
        for j in range(i+1,n):
            intradiff+=dic_cos(groupcounts[t+'_'+str(i)], groupcounts[t+'_'+str(j)])
    print 'average intragroup difference for', t, ':',str(intradiff/3)
    print
    for l in range(k+1, len(topics)):
        interdiff = 0
        t2 = topics[l]
        for i in range(n):
            for j in range(n):
                interdiff+=dic_cos(groupcounts[t+'_'+str(i)], groupcounts[t2+'_'+str(j)])
        print 'average intergroup difference for', t,t2, ':',str(interdiff/9)
    print
