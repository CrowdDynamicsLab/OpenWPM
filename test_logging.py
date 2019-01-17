from __future__ import absolute_import
from automation import TaskManager, CommandSequence
import os



# The list of sites that we wish to crawl


sites = ['http://www.drudgereport.com', 'https://www.vox.com']




manager_params, browser_params = TaskManager.load_default_params()


# Update browser configuration (use this for per-browser settings)

# Record HTTP Requests and Responses
browser_params[0]['http_instrument'] = True
# Enable flash for all three browsers
browser_params[0]['disable_flash'] = False
browser_params[0]['save_json'] = True
browser_params[0]['cookie_instrument'] = True
browser_params[0]['profile_archive_dir'] = "profiles/"


# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '../crawl_data'
manager_params['log_directory'] = '../crawl_data'


if __name__ == "__main__":
    manager = TaskManager.TaskManager(manager_params, browser_params)
    for site in sites:
        command_sequence = CommandSequence.CommandSequence(site)
        command_sequence.get(sleep=5, timeout=100)

        command_sequence.dump_profile_cookies(120)
        manager.execute_command_sequence(command_sequence, index='**')
    manager.close()
