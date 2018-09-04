from __future__ import absolute_import
from adblockparser import AdblockRules
from automation import TaskManager, CommandSequence
from six.moves import range
import re
import sqlite3
import time

DB_FILE = "../crawl_data/ad-archive.sqlite"
MAX_SITE_VISITS = 6

# The list of sites that we wish to crawl

# Loads the manager preference and 3 copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(1)

# Update browser configuration (use this for per-browser settings)

# Record HTTP Requests and Responses
browser_params[0]['http_instrument'] = True
# Enable flash for all three browsers
browser_params[0]['disable_flash'] = False
# browser_params[i]['js_instrument'] = True
# browser_params[i]['save_all_content'] = True
# browser_params[i]['cookie_instrument'] = True
# browser_params[i]['cp_instrument'] = True

# browser_params[0]['headless'] = True  # Launch only browser 0 headless

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '~/projects/ad-archive'
manager_params['log_directory'] = '~/projects/ad-archive'


def login(manager, site):
    command_sequence = CommandSequence.CommandSequence(site)

    # Start by visiting the page
    command_sequence.get(sleep=1, timeout=6000)
    command_sequence.login_colo(timeout=600)

    # index='**' synchronizes visits between the three browsers
    manager.execute_command_sequence(command_sequence, index='**')

def process(manager, pagenum=0):
    if pagenum > 0:
        page = "https://www.coloribus.com/adsarchive/prints/?filters=%7B%22Media%22%3A%5B%221%22%5D%7D&order=date&page={}&referrerUrlPath=%2Fadsarchive%2Fprints%2F".format(pagenum)
    else:
        page = "https://www.coloribus.com/adsarchive/prints/?filters=%7B%22Media%22%3A%5B%221%22%5D%7D&order=date&page=1&referrerUrlPath=%2Fadsarchive%2Fprints%2F"
    command_sequence = CommandSequence.CommandSequence(page)
    # Start by visiting the page
    command_sequence.get(sleep=1, timeout=6000)
    command_sequence.process_colo(timeout=600)

    manager.execute_command_sequence(command_sequence, index='**')

if __name__ == "__main__":
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(manager_params, browser_params)

    login(manager, "http://www.coloribus.com")
    for page in range(41, 60):
        process(manager, page)
    # Shuts down the browsers and waits for the data to finish logging
    manager.close()
