from __future__ import absolute_import
from adblockparser import AdblockRules
from automation import TaskManager, CommandSequence
from six.moves import range
import re
import sqlite3
import time

RULE_FILE = 'easylist.txt'
DB_FILE = "../crawl_data/crawl-data.sqlite"

# The list of sites that we wish to crawl
NUM_BROWSERS = 1
VISITS_PER_SITE = 100
sites = ['http://www.washingtonpost.com',
         'http://www.theatlantic.com',         
         'http://www.thehill.com',         
         'http://www.wsj.com',    
         'http://www.nytimes.com',
         'http://www.breitbart.com']

# Loads the manager preference and 3 copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    browser_params[i]['http_instrument'] = True
    # Enable flash for all three browsers
    browser_params[i]['disable_flash'] = False
    #browser_params[i]['js_instrument'] = True
    #browser_params[i]['save_all_content'] = True
    #browser_params[i]['cookie_instrument'] = True
    #browser_params[i]['cp_instrument'] = True

# browser_params[0]['headless'] = True  # Launch only browser 0 headless

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '~/projects/crawl_data'
manager_params['log_directory'] = '~/projects/crawl_data'


def get_site_name(url):
    url = url.replace('/', '-')
    if url.find('https') != -1:
        return url[8:]
    elif url.find('http') != -1:
        return url[7:]
    else:
        return url


def visit_site(manager, site):
    save_name = get_site_name(site)
    command_sequence = CommandSequence.CommandSequence(site, reset=True)

    # Start by visiting the page
    command_sequence.get(sleep=20, timeout=90)
    command_sequence.extract_links(timeout=90)
    command_sequence.recursive_dump_page_source_to_db(timeout=90)
    command_sequence.extract_iframes(timeout=90)
    command_sequence.dump_profile_cookies(120)

    # index='**' synchronizes visits between the three browsers
    manager.execute_command_sequence(command_sequence, index='**')




if __name__ == "__main__":
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(manager_params, browser_params)
    
    for site in sites:
        for i in range(VISITS_PER_SITE):
            visit_site(manager, site)
            time.sleep(30)
    
    # Shuts down the browsers and waits for the data to finish logging
    manager.close()
