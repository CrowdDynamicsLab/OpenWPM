from __future__ import absolute_import
from adblockparser import AdblockRules
from automation import TaskManager, CommandSequence
from six.moves import range

RULE_FILE = '/home/charles/projects/OpenWPM/easylist.txt'
# The list of sites that we wish to crawl
NUM_BROWSERS = 1
sites = ['http://www.washingtonpost.com',
         # 'http://www.theatlantic.com',
         'http://www.drudgereport.com/',
         # 'http://www.thehill.com',
         # 'http://www.washingtonpost.com',
         # 'http://www.wsj.com',
         # 'http://www.breitbart.com',
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

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(manager_params, browser_params)


def get_site_name(url):
    url = url.replace('/', '-')
    if url.find('https') != -1:
        return url[8:]
    elif url.find('http') != -1:
        return url[7:]
    else:
        return url


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


def get_adblock_rules(rulefilename):
    ruletext = parse_rulefile(rulefilename)
    rules = AdblockRules(ruletext, use_re2=False)
    return rules


rules = get_adblock_rules(RULE_FILE)
# Visits the sites with all browsers simultaneously
for site in sites:
    save_name = get_site_name(site)
    command_sequence = CommandSequence.CommandSequence(site)

    # Start by visiting the page
    command_sequence.get(sleep=5, timeout=60000)

    # command_sequence.dump_page_source('{}.src'.format(save_name))

    # command_sequence.save_screenshot('{}.png'.format(save_name), timeout=30)

    # command_sequence.extract_links(timeout=30)
    command_sequence.recursive_dump_page_source_to_db()
    command_sequence.extract_iframes()
    command_sequence.get_ad_images_recursively(rules)
    # command_sequence.recursive_dump_page_source("", timeout=60000)
    #command_sequence.screenshot_iframes_containing_ads_recursively(rules, timeout=60000)
    # dump_profile_cookies/dump_flash_cookies closes the current tab.
    command_sequence.dump_profile_cookies(120)

    # index='**' synchronizes visits between the three browsers
    manager.execute_command_sequence(command_sequence, index='**')

# Shuts down the browsers and waits for the data to finish logging
manager.close()
