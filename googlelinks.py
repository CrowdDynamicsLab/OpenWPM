from __future__ import absolute_import
from automation import TaskManager, CommandSequence
from six.moves import range
import sqlite3
import time

manager_params, browser_params = TaskManager.load_default_params(1)

browser_params[0]['http_instrument'] = True
# Enable flash for all three browsers
browser_params[0]['disable_flash'] = False


def process_search(manager, topic, pages):
    p = "https://www.google.com/search?q="+topic
    command_sequence = CommandSequence.CommandSequence(p)
    command_sequence.get(sleep=1, timeout=10000)
    command_sequence.process_google(pages)
    manager.execute_command_sequence(command_sequence, index='**')
    time.sleep(1)


if __name__ == "__main__":
    manager = TaskManager.TaskManager(manager_params, browser_params)
    topics = ['golf', 'women fashion', 'camping']
    for topic in topics:
        process_search(manager, topic, 20)
    manager.close()
    time.sleep(1000)
