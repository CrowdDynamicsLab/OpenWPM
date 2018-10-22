from __future__ import absolute_import
from automation import TaskManager, CommandSequence
import os





# The list of sites that we wish to crawl

VISITS_PER_SITE = 10
sites = ['http://www.washingtonpost.com',
         'http://www.breitbart.com']

PROFILE_TAR = "profiles/"

# Loads the manager preference and 3 copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params()


# Update browser configuration (use this for per-browser settings)

# Record HTTP Requests and Responses
browser_params[0]['http_instrument'] = True
# Enable flash for all three browsers
browser_params[0]['disable_flash'] = False
# browser_params[i]['js_instrument'] = True
# browser_params[i]['save_all_content'] = True
browser_params[0]['cookie_instrument'] = True
browser_params[0]['profile_archive_dir'] = "profiles/"
# browser_params[i]['cp_instrument'] = True

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '../crawl_data'
manager_params['log_directory'] = '../crawl_data'

if os.path.isfile(PROFILE_TAR + 'profile.tar') or os.path.isfile(PROFILE_TAR + 'profile.tar.gz'):
    browser_params[0]['profile_tar'] = PROFILE_TAR

if __name__ == "__main__":
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(manager_params, browser_params)
    for site in sites:
        command_sequence = CommandSequence.CommandSequence(site)
        # command_sequence.load_profile("../crawl_data/", "../crawl_data/")
        # Start by visiting the page
        command_sequence.get(sleep=5, timeout=100)
        # command_sequence.dump_page_source('{}.src'.format(save_name))
        # command_sequence.save_screenshot('{}.png'.format(save_name), timeout=30)
        # command_sequence.extract_links(timeout=30)
        # command_sequence.recursive_dump_page_source("", timeout=60000)
        # command_sequence.screenshot_iframes_containing_ads_recursively(rules, timeout=60000)
        # dump_profile_cookies/dump_flash_cookies closes the current tab.
        command_sequence.dump_profile_cookies(120)
        # index='**' synchronizes visits between the three browsers
        manager.execute_command_sequence(command_sequence, index='**')
    # Shuts down the browsers and waits for the data to finish logging
    manager.close()
