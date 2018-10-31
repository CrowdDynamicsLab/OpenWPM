import sys
import sqlite3
import json
import pprint
import os
from bs4 import BeautifulSoup
from adblockparser import AdblockRules
from shutil import copyfile

DB_FILE = "../crawl_data/crawl-data.sqlite"
SRC_DIR = "../crawl_data/screenshots/iframes"
DST_DIR = "images/ads"
NOT_DIR = 'images/notads'

def parse_rulefile(filename):
    result = []
    with open(filename, 'r') as fi:
        line = fi.readline().strip()
        while line != '':
            if line[0] != '!' and line[0] != '[':                    
                result.append(line)
            line = fi.readline().strip()
    print 'loaded rulefile with {} rules'.format(len(result))
    return result


def query_source_for_frame(rules, frame_id):
    conn = sqlite3.connect(DB_FILE)
    request_tuples = conn.execute("SELECT af.frame_id from ads_found AS af WHERE af.frame_id='{}'".format(frame_id)).fetchall()
    if len(request_tuples) == 0:
        return False
    else:
        return True


def get_requests_from_database():
    conn = sqlite3.connect(DB_FILE)
    request_tuples = conn.execute('SELECT url FROM http_requests').fetchall()
    return [t[0] for t in request_tuples]
    

def check_requests_in_database(rules):
    requests = get_requests_from_database()
    print 'got {} requests, checking now'.format(len(requests))
    for request in requests:
        #print request
        if rules.should_block(request):
            print "should block {}".format(request)


def get_adblock_rules(rulefilename):
    ruletext = parse_rulefile(rulefilename)
    rules = AdblockRules(ruletext, use_re2=False)
    return rules


def analyze_source(conn, rules, source):
    for frame_id, next_source in source['iframes'].iteritems():
        #  what we will have after running this recursively is an entry in the ads_found table for every child iframe
        #  that sets off the ad blocker as well as one for each of its parents up to the root document
        if analyze_recurse(conn, rules, next_source, frame_id, 0):
            conn.execute('INSERT INTO ads_found (frame_id, frame_source, depth, have_image) VALUES (?, ?, ?, ?)', (frame_id, json.dumps(next_source), 0, False))
            conn.commit()



def analyze_recurse(conn, rules, source, frame_id, depth):
    frame_source = source['source']
    frame_soup = BeautifulSoup(frame_source, 'html.parser')
    a_list = frame_soup.find_all('a')
    for a in a_list:
        a_href = a.get('href')
        if a_href:
            # one of my hrefs is an ad            
            if rules.should_block(a_href):
                #print 'ad_a_href: {}'.format(a_href)
                #conn.execute('INSERT INTO ads_found (frame_id, frame_source) VALUES (?, ?)', (frame_id, json.dumps(source)))
                #conn.commit()
                return True

    iframe_list = frame_soup.find_all('iframe')
    for iframe in iframe_list:
        iframe_src = iframe.get('src')
        if iframe_src:
            # one of my iframe sources is an ad
            if rules.should_block(iframe_src):
                #print 'ad_iframe_src: {}'.format(iframe_src)
                #conn.execute('INSERT INTO ads_found (frame_id, frame_source) VALUES (?, ?)', (frame_id, json.dumps(source)))
                #conn.commit()
                return True

    img_list = frame_soup.find_all('img')            
    for img in img_list:
        img_src = img.get('src')
        if img_src:
            # one of my images is an ad
            if rules.should_block(img_src):
                #print 'ad_img_src: {}'.format(img_src)
                #conn.execute('INSERT INTO ads_found (frame_id, frame_source) VALUES (?, ?)', (frame_id, json.dumps(source)))
                #conn.commit()
                return True

    for next_frame_id, next_source in source['iframes'].iteritems():
        # one of my children iframes contains an ad
        if analyze_recurse(conn, rules, next_source, next_frame_id, depth+1):
            conn.execute('INSERT INTO ads_found (frame_id, parent_frame_id, frame_source, depth, have_image) VALUES (?, ?, ?, ?, ?)', (next_frame_id, frame_id, json.dumps(next_source), depth + 1, False))
            conn.commit()
            return True
    return False


def populate_database(rules):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DROP TABLE IF EXISTS ads_found")
    conn.commit()
    conn.execute("CREATE TABLE IF NOT EXISTS ads_found (frame_id TEXT UNIQUE, parent_frame_id TEXT, frame_source TEXT, depth INT, have_image BOOL)")
    source_tuples = conn.execute('SELECT source FROM recursive_source').fetchall()
    sources = [t[0] for t in source_tuples]
    for source in sources:
        # find every frameid which either itself or its children has an ad in it
        source_dict = json.loads(source)
        analyze_source(conn, rules, source_dict)


def find_ads(rules):
    populate_database(rules)
    conn = sqlite3.connect(DB_FILE)
    print 'datbase has been populated with ad iframes'
    for host in os.listdir(SRC_DIR):
        if not os.path.exists("{}/{}".format(DST_DIR, host)):
            os.makedirs("{}/{}".format(DST_DIR, host))
        if not os.path.exists("{}/{}".format(NOT_DIR, host)):
            os.makedirs("{}/{}".format(NOT_DIR, host))
        for filename in os.listdir('{}/{}'.format(SRC_DIR, host)):
            statinfo = os.stat('{}/{}/{}'.format(SRC_DIR, host, filename))            
            frame_id = filename[:-4]
            #if statinfo.st_size > 5000 and query_source_for_hash(rules, file_hash):
            if statinfo.st_size > 5000 and query_source_for_frame(rules, frame_id):
                conn.execute("UPDATE ads_found SET have_image=? WHERE frame_id=?", (True, frame_id))
                conn.commit()
                copyfile("{}/{}/{}".format(SRC_DIR, host, filename), "{}/{}/{}".format(DST_DIR, host, filename))
            elif query_source_for_frame(rules, frame_id):
                conn.execute("UPDATE ads_found SET have_image=? WHERE frame_id=?", (True, frame_id))
                conn.commit()
                copyfile("{}/{}/{}".format(SRC_DIR, host, filename), "{}/{}/{}".format(NOT_DIR, host, filename))
            else:
                copyfile("{}/{}/{}".format(SRC_DIR, host, filename), "{}/{}/{}".format(NOT_DIR, host, filename))



if __name__ == "__main__":
    print >> sys.stderr, "usage: python {} <rulefile> <filehash>".format(sys.argv[0])
    rules = get_adblock_rules(sys.argv[1])
    find_ads(rules)