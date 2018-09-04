import sqlite3
import re

DB_FILE = "../crawl_data/crawl-data.sqlite"

def get_sites_to_visit_from_db():
    sites_to_visit = []
    conn = sqlite3.connect(DB_FILE)
    link_tuples = conn.execute('SELECT found_on, location FROM links_found').fetchall()
    for link in link_tuples:
        found_on = link[0]
        location = link[1]
        if not location:
            continue
        if found_on.find('washingtonpost.com') != -1:
            # do wapo filter
            pattern = r'.*washingtonpost.com/\w+/.*/\d\d\d\d/\d\d/\d\d'
            if re.search(pattern, location):
                print 'YES: {}'.format(link)
            else:
                print 'NO: {}'.format(link)

        elif found_on.find('breitbart.com') != -1:
            pass
            #do breitbart filter
        elif found_on.find('theatlantic.com') != -1:
            # do atlantic filter
            pass

    return sites_to_visit

if __name__ == "__main__":
    get_sites_to_visit_from_db()