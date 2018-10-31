import sys
import sqlite3
import json
import pprint
import os
from urlparse import urlparse
from bs4 import BeautifulSoup
from adblockparser import AdblockRules
from shutil import copyfile

DB_FILE = "../crawl_data/crawl-data.sqlite"

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



def analyze_recurse(rules, source, patriarch):
    frame_source = source['source']
    frame_soup = BeautifulSoup(frame_source, 'html.parser')
    a_list = frame_soup.find_all('a')
    for a in a_list:
        a_href = a.get('href')
        if a_href:
            if rules.should_block(a_href):
                print 'ad_a_href: {}'.format(a_href)
                return True

    iframe_list = frame_soup.find_all('iframe')
    for iframe in iframe_list:
        iframe_src = iframe.get('src')
        if iframe_src:
            if rules.should_block(iframe_src):
                print 'ad_iframe_src: {}'.format(iframe_src)
                return True

    img_list = frame_soup.find_all('img')            
    for img in img_list:
        img_src = img.get('src')
        if img_src:
            if rules.should_block(img_src):
                print 'ad_img_src: {}'.format(img_src)
                return True
    for frame_id, next_source in source['iframes'].iteritems():
        if analyze_recurse(rules, next_source, patriarch):
            return True
    return False

def query_source_for_hash(rules, query_file_hash):
    conn = sqlite3.connect(DB_FILE)
    source_tuples = conn.execute('SELECT rs.source FROM iframes_found AS if JOIN site_visits AS sv on if.found_on=sv.site_url JOIN recursive_source AS rs on rs.visit_id=sv.visit_id WHERE if.file_hash="{}"'.format(query_file_hash)).fetchall()
    if len(source_tuples) != 1:
        print 'source_tuples length is not equal to 1'
        return
    source = source_tuples[0][0]
    frame_ids_with_ads = []
    source_dict = json.loads(source)    
    for frame_id, frame_source in source_dict['iframes'].iteritems():
        if analyze_recurse(rules, frame_source, frame_id):
            print 'found ad for frame_id: {}'.format(frame_id)
            frame_ids_with_ads.append(frame_id)
    print frame_ids_with_ads
            
def find_ads(rules):
    pass

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

if __name__ == "__main__":
    print >> sys.stderr, "usage: python {} <rulefile>".format(sys.argv[0])
    rules = get_adblock_rules(sys.argv[1])
    find_ads(rules)