from PIL import Image
import imagehash
import os
import sqlite3
import shutil

f = 'camping_0'
ADS_DIRECTORY = "/home/nick/Development/crawl_data/"+f+"/allads/"
DB_FILE = "/home/nick/Development/crawl_data/"+f+ "/crawl-data.sqlite"
base = "/home/nick/Development/crawl_data/"+f
DIR  = "/home/nick/Development/crawl_data/"+f+'/images/findads/'
groups = base+'/hashgroups/'
def grab_images():
    if 'allads' not in os.listdir(base):
        os.mkdir(ADS_DIRECTORY)
    for folder in os.listdir(DIR):
        for img in os.listdir(DIR+folder):
            path = DIR+folder+'/'+img
            shutil.copy2(path, ADS_DIRECTORY+img)

def find_similar_images():
    images = {}
    if 'hashgroups' not in os.listdir(base):
        os.mkdir(groups)
    for img_file in os.listdir(ADS_DIRECTORY):
        try:
            hash = imagehash.average_hash(Image.open(os.path.join(ADS_DIRECTORY, img_file)))
        except:
            continue
        if hash not in images:
            images[hash] = []

        images[hash].append(img_file)
    conn = sqlite3.connect(DB_FILE)
    print(len(images))
    for hash in images:
        os.mkdir(groups+str(hash))
        for img in images[hash]:
            shutil.copy2(ADS_DIRECTORY+'/'+img, groups+'/'+str(hash)+'/'+img)
    '''
    for k, imgs in images.iteritems():
        uid = imgs[0][:-4]
        for img in imgs:
            conn.execute('UPDATE ads_found SET uid=? WHERE frame_id=?',
                         (uid, img[:-4]))
            conn.commit()
    '''


# the plan is to go through every image, load them up
# fingerprint them, and de-dup if distance is below a threshold
# we can then add a unique id to each ad in the ads_found db table
if __name__ == "__main__":
    flist = ['golf','camping', 'women fashion']
    for topic in flist:
        for i in range(3):
            f = topic+'_'+str(i)
            ADS_DIRECTORY = "/home/nick/Development/crawl_data/"+f+"/allads/"
            DB_FILE = "/home/nick/Development/crawl_data/"+f+ "/crawl-data.sqlite"
            base = "/home/nick/Development/crawl_data/"+f
            DIR  = "/home/nick/Development/crawl_data/"+f+'/images/findads/'
            groups = base+'/hashgroups/'
            grab_images()
            find_similar_images()
