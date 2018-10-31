'''
Nicholas Chen

Converts images to numpy arrays and saves output to decrease load times when training
'''

import pickle
import numpy as np
from PIL import Image
from scipy import ndimage
from sklearn.model_selection import train_test_split


import os
import shutil
import imtools
from scipy.cluster.vq import *
from sklearn import preprocessing as prep
from sklearn.cluster import KMeans
from time import time
from sklearn.decomposition import PCA
from sklearn import metrics
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency

subs = ['camping','golf', 'women fashion']

ydim = 64
xdim = 64

###Uses iframes for each sub located in crawl_data, generates np arrays of the images and path to the images
def convert_imgs():
	count = 0
	paths = []
	imgs = []
	for sub in subs:
		dir = "crawl_data/" + sub + '/screenshots/iframes/'

		for subdir in os.listdir(dir):
			for fname in os.listdir(dir+subdir):
				statinfo = os.stat(dir+subdir + '/'+fname)
				if('.png' not in fname) or statinfo.st_size == 0:
					continue
				img = Image.open(dir+subdir + '/'+fname)
				img = np.array(img.resize((ydim,xdim))).flatten()
				imgs.append(img)
				paths.append(dir+subdir + '/'+fname)

	return imgs,paths


imgs, paths = convert_imgs()
imgs = prep.scale(imgs)


pca = PCA(n_components=6)


for clusters in [32,64]: #numbers of clusters to try
	x = pca.fit(imgs).transform(imgs)
	kmeans = KMeans(init ='k-means++', n_clusters = clusters)
	kmeans.fit(x)

	labels = kmeans.labels_

	for i in range(len(kmeans.cluster_centers_)):
		if 'center_'+str(i) not in os.listdir('clustering/'):
			os.mkdir('clustering/center_'+str(i))
	if clusters == 64:
		for i in range(len(paths)):
			shutil.copy2(paths[i], 'clustering/center_'+str(labels[i]))
	sub_hist = {}
	for sub in subs:
		sub_hist[sub] = []
		for i in range(clusters):
			sub_hist[sub].append(0)
	print(labels)
	print(paths)
	for i in range(len(x)):
		sub_hist[paths[i].split('/')[1]][labels[i]] +=1
		#shutil.copy2(paths[i], 'clustering/center_'+str(labels[i]))

	for sub in subs:
		s = np.sum(sub_hist[sub])
		sub_hist[sub] = [float(x)/float(s) for x in sub_hist[sub]]
		rem = []
		for i in range(len(sub_hist[sub])):
			if sub_hist[sub][i] > .1:
				rem.append(i)
		rem.sort(reverse=True)
		for sub in subs:
			for num in rem:
				sub_hist[sub][num] = 0
	for sub in subs:
		s = np.sum(sub_hist[sub])
		sub_hist[sub] = [float(x)/float(s) for x in sub_hist[sub]]
		plt.figure()
		plt.bar(range(clusters),sub_hist[sub])
		plt.savefig(sub+str(clusters)+'.png')

	print(sub_hist)

'''

def convert():
	x1 = os.listdir("../axisvar/")
	x2 = os.listdir("../axisnoise/")
	print("Converting training set images to image feature arrays")


	ydim = 128
	xdim = 128
	train_X = []
	count = 0
	for fname in x1:
		if('.png' in fname):

			img= Image.open('../axisvar/' + fname).convert('LA')
			img = np.array(img.resize((ydim,xdim)))
			train_X.append(img)
			count+=1
			if count%1000 == 0:
				print(count)
	train_Y = np.zeros(len(train_X)) + 1 #consider triangles to be class 1

	for fname in x2:
		if '.png' in fname:
			img = Image.open('../axisnoise/' + fname).convert('LA')
			img = np.array(img.resize((ydim,xdim)))
			train_X.append(img)
			count += 1
			if count%1000 == 0:
				print(count)



	train_Y = np.append(train_Y,np.zeros(len(train_X) - len(train_Y))) #consider everything else to be class 0
	train_X = np.array(train_X)

	train_X = train_X.astype('float32')
	train_X = train_X / 255.
	train_Y = to_categorical(train_Y)

	np.save('train_X.npy', train_X)
	np.save('train_Y.npy', train_Y)
'''
