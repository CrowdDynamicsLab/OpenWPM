from __future__ import absolute_import
from automation import TaskManager, CommandSequence
from six.moves import range
import sqlite3
import time

DB_FILE = "./tmp/crawl-data.sqlite"
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
manager_params['data_directory'] = '~/projects/ad-archive/duke'
manager_params['log_directory'] = '~/projects/ad-archive/duke'




def process_directory_page(manager, pagenum=0):    
    if pagenum == 0:
        page = 'https://repository.duke.edu/dc/adaccess?f%5Bactive_fedora_model_ssi%5D%5B%5D=Item&range%5Byear_facet_iim%5D%5Bbegin%5D=1943&range%5Byear_facet_iim%5D%5Bend%5D=1961&search_field=dummy_range&sort=date_sort_si+desc'
    else:
        page = 'https://repository.duke.edu/dc/adaccess?f%5Bactive_fedora_model_ssi%5D%5B%5D=Item&page={}&range%5Byear_facet_iim%5D%5Bbegin%5D=1943&range%5Byear_facet_iim%5D%5Bend%5D=1961&search_field=dummy_range&sort=date_sort_si+desc'.format(pagenum)
    command_sequence = CommandSequence.CommandSequence(page)
    # Start by visiting the page
    command_sequence.get(sleep=1, timeout=6000)
    # process the directory page, populating the db with the next pages to crawl
    #command_sequence.process_duke_directory(timeout=600)
    manager.execute_command_sequence(command_sequence)

if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(manager_params, browser_params)
    for i in range(260, 320):
        # parse the directory page
        process_directory_page(manager, i)
        time.sleep(20)
        # load the discovered pages from the database
        url_tuples = conn.execute("SELECT url FROM pages_found WHERE visited=0").fetchall()
        for ut in url_tuples:
            url = ut[0]
            command_sequence = CommandSequence.CommandSequence(url)
            command_sequence.get(sleep=1, timeout=6000)
            #command_sequence.process_duke_page(timeout=600)
            manager.execute_command_sequence(command_sequence)
            # conn.execute("UPDATE pages_found SET visited=1 WHERE url=?", (url, ))
            time.sleep(5)

    
    
    manager.close()
