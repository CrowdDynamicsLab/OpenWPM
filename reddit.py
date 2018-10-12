from __future__ import absolute_import
from automation import TaskManager, CommandSequence
from six.moves import range
import sqlite3
import time

manager_params, browser_params = TaskManager.load_default_params(1)

browser_params[0]['http_instrument'] = True
# Enable flash for all three browsers
browser_params[0]['disable_flash'] = False


def process_subreddit(manager, sub, pages):
    page = "https://old.reddit.com/r/" + sub + "/top/?sort=top&t=all"
    print(page)
    command_sequence = CommandSequence.CommandSequence(page)
    command_sequence.get(sleep=1, timeout=10000)
    command_sequence.process_reddit(pages)
    manager.execute_command_sequence(command_sequence, index='**')
    time.sleep(1)


if __name__ == "__main__":
    manager = TaskManager.TaskManager(manager_params, browser_params)
    subs = ['baseball', 'mma', 'christianity', 'linux', 'ethereum', 'the_donald', 'sandersforpresident']
    for sub in subs:
        process_subreddit(manager, sub, 20)

    time.sleep(1000)
