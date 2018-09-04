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



def check_correct_recursively(source, my_frame_id):
    for frame_id, next_source in source['iframes'].iteritems():
        if frame_id == my_frame_id:
            return True
        elif check_correct_recursively(next_source, my_frame_id):
            return True
    return False


# only analyze iframes that are in the correct_branch
def analyze_recurse(rules, source):
    frame_source = source['source']
    frame_soup = BeautifulSoup(frame_source, 'html.parser')
    a_list = frame_soup.find_all('a')
    for a in a_list:
        a_href = a.get('href')
        print a_href
        if a_href:
            # one of my hrefs is an ad
            if rules.should_block(a_href):
                print 'ad_a_href: {}'.format(a_href)
                return True
            else:
                print 'no ad'

    iframe_list = frame_soup.find_all('iframe')
    for iframe in iframe_list:
        iframe_src = iframe.get('src')
        print iframe_src
        if iframe_src:
            # one of my iframe sources is an ad
            if rules.should_block(iframe_src):
                print 'ad_iframe_src: {}'.format(iframe_src)
                return True
            else:
                print 'no ad'

    img_list = frame_soup.find_all('img')            
    for img in img_list:
        img_src = img.get('src')
        print img_src
        if img_src:
            # one of my images is an ad
            if rules.should_block(img_src):
                print 'ad_img_src: {}'.format(img_src)                
                return True
            else:
                print 'no ad'

    for frame_id, next_source in source['iframes'].iteritems():
        # one of my children iframes contains an ad
        if analyze_recurse(rules, next_source):            
            return True
    return False
    

def query_source_for_hash(rules, query_file_hash):
    conn = sqlite3.connect(DB_FILE)
    source_tuples = conn.execute('SELECT rs.source FROM iframes_found AS if JOIN recursive_source AS rs on rs.visit_id=if.visit_id WHERE if.file_hash="{}"'.format(query_file_hash)).fetchall()
    if len(source_tuples) != 1:
        print 'source_tuples length is not equal to 1'
        return
    source = source_tuples[0][0]    
    source_dict = json.loads(source)    

    # get the frame_id for this file_hash
    my_frame_id = conn.execute("SELECT frame_id FROM iframes_found WHERE file_hash='{}'".format(query_file_hash)).fetchall()[0][0]
    print 'my frame id is {}'.format(my_frame_id)

    for frame_id, frame_source in source_dict['iframes'].iteritems():
        if frame_id == my_frame_id:
            print 'found correct branch at top'
            analyze_recurse(rules, frame_source)
        elif check_correct_recursively(frame_source, my_frame_id):
            print 'found correct branch recursively'
            analyze_recurse(rules, frame_source)


def get_requests_from_database():
    conn = sqlite3.connect(DB_FILE)
    request_tuples = conn.execute('SELECT url FROM http_requests').fetchall()
    return [t[0] for t in request_tuples]
    
    
def get_adblock_rules(rulefilename):
    ruletext = parse_rulefile(rulefilename)
    rules = AdblockRules(ruletext)
    return rules

if __name__ == "__main__":
    print >> sys.stderr, "usage: python {} <rulefile> <filehash>".format(sys.argv[0])
    rules = get_adblock_rules(sys.argv[1])
    query_source_for_hash(rules, sys.argv[2])