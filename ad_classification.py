import sqlite3
import json
from urlparse import urlparse
import pytesseract
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
try:
    import Image
except ImportError:
    from PIL import Image


AD_ARCHIVE_FILE = "../ad-archive/duke/crawl-data.sqlite"
ARCHIVE_IMAGE_PATH = 'images/ad-archive/duke'
CRAWL_FILE = "../crawl_data/crawl-data.sqlite"
WORD_FILE = '../english-words/words.txt'
STOP_WORD_FILE = 'stopwords.txt'
cat_file = 'category_map.txt'


def get_category_dictionary():
    categories = {}
    with open(cat_file, 'r') as fi:
        line = fi.readline().strip()
        while line != '':
            line_array = line.split('\t')
            categories[line_array[0]] = line_array[1]
            line = fi.readline().strip()
    return categories


def get_archive_dictionary():
    cat_dict = get_category_dictionary()
    conn = sqlite3.connect(AD_ARCHIVE_FILE)
    ad_tuples = conn.execute("SELECT * FROM ads_found").fetchall()
    ad_dictionary = {}
    for tup in ad_tuples:
        img_src = tup[0]
        metadata = json.loads(tup[1])        
        category = metadata['Industry'][0][1:]  
        if category == u'\u0421able/Satellite television':
            continue      
        transformed_category = cat_dict[category]
        if transformed_category == '!':
            continue
        ad_dictionary[img_src] = transformed_category
    return ad_dictionary


def print_archive_category_counts():
    archive_dict = get_archive_dictionary()
    counts = {}
    for img_src, category in archive_dict.iteritems():        
        if category not in counts:
            counts[category] = 0
        counts[category] += 1
    for cat, count in counts.iteritems():
        print '{}\t{}'.format(cat.encode('utf8'), count)


def get_words(word_file):
    words = set([])
    with open(word_file, 'r') as fi:
        line = fi.readline().strip()
        while line != '':
            words.add(line)
            line = fi.readline().strip()
    return words


def get_img_file_text(allowed_words, stop_words, filename):
    allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    caps_str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    allowed_set = set([c for c in allowed_chars])
    caps_set = set([c for c in caps_str])
    img_string = pytesseract.image_to_string(Image.open('{}/{}'.format(ARCHIVE_IMAGE_PATH, filename)), lang="eng").encode('utf-8')    

    img_array = img_string.decode('utf-8').split()        
    processed_img_array = []
    for word in img_array:
        processed_word = ''
        for char in word:
            if char not in allowed_set:
                continue
            else:
                processed_word = processed_word + char
        if processed_word != '':
            if processed_word.lower() in allowed_words:
                if processed_word.lower() not in stop_words:
                    processed_img_array.append(processed_word)
    img_string2 = ' '.join(processed_img_array)    
    return img_string2.lower()


def get_archive_image_text_and_category_dictionary(filename=None):
    if filename:
        return pickle.load(open(filename, 'rb'))
    text_cat_dict = {}
    archive_dict = get_archive_dictionary()
    allowed_words = get_words(WORD_FILE)
    stop_words = get_words(STOP_WORD_FILE)
    for img_src, category in archive_dict.iteritems():
        filename = urlparse(img_src).path.split('/')[-1]
        filetext = get_img_file_text(allowed_words, stop_words, filename)
        text_cat_dict[filename] = {}
        text_cat_dict[filename]['category'] = category
        text_cat_dict[filename]['text'] = filetext
        print '{}\t{}\t{}'.format(filename, category, filetext)
    return text_cat_dict



def get_all_words_in_archive(archive_dict):
    words = {}
    count = 0
    for img_src, meta in archive_dict.iteritems():        
        for word in meta['text'].split():
            if word not in words:
                words[word] = count
                count += 1
    return words


def train_classifier():
    text_cat_dict = get_archive_image_text_and_category_dictionary(filename='text_cat.dict')
    words = get_all_words_in_archive(text_cat_dict)
    X = []
    Y = []
    for img_src, meta in text_cat_dict.iteritems():
        if len(meta['text'].split()) == 0:
            continue
        next_data_item = [0 for k in words.keys()]
        for word in meta['text'].split():
            index = words[word]
            next_data_item[index] = 1
        X.append(next_data_item)
        Y.append(meta['category'])
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.15, random_state=420)
    clf = RandomForestClassifier(max_depth=10, random_state=0)
    clf.fit(X_train, Y_train)
    Y_pred = clf.predict(X_test)
    print accuracy_score(Y_test, Y_pred)
    print classification_report(Y_test, Y_pred)
    print confusion_matrix(Y_test, Y_pred)


if __name__ == "__main__":
    train_classifier()
