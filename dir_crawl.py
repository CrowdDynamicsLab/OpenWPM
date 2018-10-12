from __future__ import absolute_import
from adblockparser import AdblockRules
from automation import TaskManager, CommandSequence
from six.moves import range
import re
import sqlite3
import time
import pandas as pd
import numpy as np

RULE_FILE = 'easylist.txt'
DB_FILE = "../crawl_data/crawl-data.sqlite"
MAX_SITE_VISITS = 6

# The list of sites that we wish to crawl
NUM_BROWSERS = 1



# Loads the manager preference and 3 copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    #browser_params[i]['http_instrument'] = True
    # Enable flash for all three browsers
    browser_params[i]['disable_flash'] = True
    #browser_params[i]['js_instrument'] = True
    #browser_params[i]['save_all_content'] = True
    #browser_params[i]['cookie_instrument'] = True
    #browser_params[i]['cp_instrument'] = True

# browser_params[0]['headless'] = True  # Launch only browser 0 headless

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '../crawl_data'
manager_params['log_directory'] = '../crawl_data'


def get_site_name(url):
    url = url.replace('/', '-')
    if url.find('https') != -1:
        return url[8:]
    elif url.find('http') != -1:
        return url[7:]
    else:
        return url


def visit_site(manager, site):
    #save_name = get_site_name(site)
    command_sequence = CommandSequence.CommandSequence(site)

    # Start by visiting the page
    command_sequence.get(sleep=5, timeout=90)
    #command_sequence.extract_links(timeout=90)
    #command_sequence.recursive_dump_page_source_to_db(timeout=90)
    #command_sequence.extract_iframes(timeout=90)  #do this on every page
    #command_sequence.dump_profile_cookies(120)

    # index='**' synchronizes visits between the three browsers
    manager.execute_command_sequence(command_sequence, index='**')

def get_ads(manager):
    command_sequence = CommandSequence.CommandSequence("https://cnn.com")
    command_sequence.get(sleep=5, timeout=90)
    command_sequence.extract_iframes(timeout=90)
    manager.execute_command_sequence(command_sequence, index='**')

def get_sites_to_visit_from_db():
    sites_to_visit = []
    conn = sqlite3.connect(DB_FILE)
    link_tuples = conn.execute('SELECT found_on, location FROM links_found').fetchall()
    visit_count_dictionary = {}
    for link in link_tuples:
        found_on = link[0]
        location = link[1]
        if not location:
            continue
        if found_on.find('washingtonpost.com') != -1:
            if 'wapo' not in visit_count_dictionary:
                visit_count_dictionary['wapo'] = 1
            if visit_count_dictionary['wapo'] >= MAX_SITE_VISITS:
                continue
            # do wapo filter
            pattern = r'.*washingtonpost.com/.*/\d\d\d\d/\d\d/\d\d'
            if re.search(pattern, location):
                sites_to_visit.append(location)
                visit_count_dictionary['wapo'] += 1

        elif found_on.find('breitbart.com') != -1:
            if 'breitbart' not in visit_count_dictionary:
                visit_count_dictionary['breitbart'] = 1
            if visit_count_dictionary['breitbart'] >= MAX_SITE_VISITS:
                continue
            #do breitbart filter
            pattern = r'.*breitbart.com/.*/\d\d\d\d/\d\d/\d\d'
            if re.search(pattern, location):
                sites_to_visit.append(location)
                visit_count_dictionary['breitbart'] += 1

        elif found_on.find('theatlantic.com') != -1:
            if 'atlantic' not in visit_count_dictionary:
                visit_count_dictionary['atlantic'] = 1
            if visit_count_dictionary['atlantic'] >= MAX_SITE_VISITS:
                continue
            # do atlantic filter
            pattern = r'.*theatlantic.com/.*/\d\d\d\d/\d\d'
            if re.search(pattern, location):
                sites_to_visit.append(location)
                visit_count_dictionary['atlantic'] += 1

    return sites_to_visit

###List of subreddit csvs to crawl on - nick
subs = ['baseball','MMA','Christianity']
if __name__ == "__main__":
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    for sub in subs:
        DB_FILE = "../crawl_data/"+sub+".sqlite"
        sites = []
        manager = TaskManager.TaskManager(manager_params, browser_params)
        command_sequence = CommandSequence.CommandSequence('https://google.com')

        ###commands I wrote to log in to my dummy profile and clear its entire history - nick
        command_sequence.google_login()
        command_sequence.clear_google()
        manager.execute_command_sequence(command_sequence,index = '**')
        time.sleep(30)
        linkdf = pd.read_csv('./sublinks/' + sub + '.csv')

        ###i is the number of pages to randomly select and visit 0 - nick
        for i in range(10):
            sites.append(linkdf.iloc[int(np.random.random()*len(linkdf))][0])

        command_sequence = CommandSequence.CommandSequence('https://google.com')

        ###visit_sites() takes a list of urls and visits them all sequentially - nick
        command_sequence.visit_sites(sites)
        manager.execute_command_sequence(command_sequence,index = '**')

        ###add a sleep so only one crawl is going on at a time - nick
        time.sleep(120)

        for i in range(3):
            get_ads(manager)
        time.sleep(30)
        #subsequent_visits = get_sites_to_visit_from_db()
        print 'now visiting subsequent sites'
        #print subsequent_visits
        #for site in subsequent_visits:
        #    visit_site(manager, site)

        # Shuts down the browsers and waits for the data to finish logging
        manager.close()
    
