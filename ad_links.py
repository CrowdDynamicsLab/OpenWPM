import sqlite3
import json
from bs4 import BeautifulSoup
from urlparse import urljoin

DB_FILE = "../crawl_data/crawl-data.sqlite"


def find_links_in_source_recursively(frame_id, source, found_on):
    conn = sqlite3.connect(DB_FILE)
    frame_source = source['source']
    frame_soup = BeautifulSoup(frame_source, 'html.parser')
    a_list = frame_soup.find_all('a')
    for a in a_list:
        a_href = a.get('href')
        if a_href:
            conn.execute("INSERT INTO ad_links (frame_id, link) VALUES(?, ?)", (frame_id, urljoin(found_on, a_href)))
            conn.commit()
    for next_frame_id, next_source in source['iframes'].iteritems():
        # i'm going to call this with frame_id rather than next_frame_id so that the top level frame_id are the only
        # ones inserted into the db, since the ad image files have a filename associated with the top level frame id
        # only
        find_links_in_source_recursively(frame_id, next_source, found_on)


def get_ads_from_db():
    conn = sqlite3.connect(DB_FILE)
    ad_tuples = conn.execute('SELECT af.frame_id, af.frame_source, if.found_on FROM ads_found AS af JOIN iframes_found AS if on if.frame_id=af.frame_id WHERE af.depth=0').fetchall()
    for tuple in ad_tuples:
        frame_id = tuple[0]
        source = json.loads(tuple[1])
        found_on = tuple[2]
        find_links_in_source_recursively(frame_id, source, found_on)

if __name__ == "__main__":
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DROP TABLE IF EXISTS ad_links")
    conn.commit()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS ad_links (frame_id TEXT, link TEXT)")
    get_ads_from_db()