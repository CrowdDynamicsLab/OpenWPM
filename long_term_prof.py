from __future__ import absolute_import
from adblockparser import AdblockRules
from automation import TaskManager, CommandSequence
from six.moves import range
import re
import sqlite3
import time
import pandas as pd
import numpy as np
import os
from shutil import copyfile
RULE_FILE = 'easylist.txt'
DB_FILE = "../crawl_data/crawl-data.sqlite"

# The list of sites that we wish to crawl
NUM_BROWSERS = 1



# Loads the manager preference and 3 copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    # Enable flash for all three browsers
    browser_params[i]['disable_flash'] = True
    browser_params[i]['http_instrument'] = True
    #browser_params[i]['save_all_content'] = True
    #browser_params[i]['save_JSON'] = True

def visit_site(manager, site):
    #save_name = get_site_name(site)
    command_sequence = CommandSequence.CommandSequence(site)

    # Start by visiting the page
    command_sequence.get(sleep=5, timeout=15)
    #command_sequence.extract_links(timeout=90)
    #command_sequence.recursive_dump_page_source_to_db(timeout=90)
    #command_sequence.extract_iframes(timeout=90)  #do this on every page
    #command_sequence.dump_profile_cookies(120)

    # index='**' synchronizes visits between the three browsers
    manager.execute_command_sequence(command_sequence, index='**')

def get_ads(manager, sites):
    for i in range(1):
        for site in sites:
            command_sequence = CommandSequence.CommandSequence(site, reset = False)
            command_sequence.get(sleep=5, timeout=60)
            command_sequence.recursive_dump_page_source_to_db(timeout=90)
            #command_sequence.extract_iframes(timeout=90)
    manager.execute_command_sequence(command_sequence, index='**')

###List of subreddit csvs to crawl on - nick
#
if __name__ == "__main__":
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    sub = 'camping'
    base = '/home/nick/Development/crawl_data/long_term/'
    if sub not in os.listdir(base):
        os.mkdir(base+sub)
    l = 0
    linkdf = pd.read_csv('/home/nick/Development/OpenWPM/googlinks/' + sub + '.csv')
    while True:
        manager_params['data_directory'] = base+sub
        manager_params['log_directory'] = base+sub
        if i > 0:
            browser_params[0]['profile_archive_dir'] = base+sub+'/'
            browser_params[0]['profile_tar'] = base+sub+'/'
        sites = []
        ###i is the number of pages to randomly select and visit 0 - nick
        manager = TaskManager.TaskManager(manager_params, browser_params)
        for i in range(20):
            sites.append(linkdf.iloc[int(np.random.random()*len(linkdf))][0])
        command_sequence = CommandSequence.CommandSequence('https://google.com', reset = False)
        for i in range(0, len(sites)):
            command_sequence.visit_sites([sites[i]])
        command_sequence.dump_profile(dump_folder = base+sub)

        manager.execute_command_sequence(command_sequence, index = '**')
        time.sleep(500)
        manager.close()
        time.sleep(7200)
        copyfile(base+sub+'/profile.tar.gz', base+sub+'/profile_' + str(l) + '.tar.gz')
        l+=1
        #print subsequent_visits
        #for site in subsequent_visits:
        #    visit_site(manager, site)

        # Shuts down the browsers and waits for the data to finish logging
        #manager.close()
