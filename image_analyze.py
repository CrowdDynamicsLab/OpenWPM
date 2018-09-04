
try:
    import Image
except ImportError:
    from PIL import Image
import pytesseract
import os
from autocorrect import spell
import sqlite3

DB_FILE = "../crawl_data/crawl-data.sqlite"
IMG_DIR = "images/ads"
WORD_FILE = '../english-words/words.txt'
allowed_words = set([])
with open(WORD_FILE, 'r') as fi:
    line = fi.readline().strip() != ''
    while line != '':        
        allowed_words.add(line)
        line = fi.readline().strip()

allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
caps_str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
caps = set([])
for char in caps_str:
    caps.add(char
        )
allowed_set = set([])
for char in allowed_chars:
    allowed_set.add(char)



conn = sqlite3.connect(DB_FILE)
conn.execute("DROP TABLE IF EXISTS ad_text")
conn.commit()
conn.execute(
    "CREATE TABLE IF NOT EXISTS ad_text (frame_id TEXT, ad_text TEXT)")

for host in os.listdir(IMG_DIR):    
    for filename in os.listdir('{}/{}'.format(IMG_DIR, host)):
        frame_id = filename.split('.')[0]
        print '{}/{}'.format(host, filename)
        img_string = pytesseract.image_to_string(Image.open('{}/{}/{}'.format(IMG_DIR, host, filename)), lang="eng").encode('utf-8')    
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
                if processed_word[0] in caps or processed_word.lower() in allowed_words:
                    processed_img_array.append(processed_word)

        img_string2 = ' '.join(processed_img_array)
        
        conn.execute("INSERT INTO ad_text (frame_id, ad_text) VALUES (?, ?)", (frame_id, img_string2))
        conn.commit()
        #img_array2 = [spell(w) for w in img_array]
        #img_string2 = ' '.join(img_array2)
        #print img_string2