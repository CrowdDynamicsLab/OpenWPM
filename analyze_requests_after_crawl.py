import sqlite3
import urllib
from urlparse import urlparse
from pprint import pprint

DB_FILE = "../crawl_data/crawl-data.sqlite"
conn = sqlite3.connect(DB_FILE)


def get_host_from_url_robust(url):
    # krxd occasionally tries to load a page http://tag/blah
    url_array = urlparse(url).hostname.split('.')
    if len(url_array) < 2:
        return urlparse(url).hostname
    return url_array[-2]

def check_row_for_leakage(row, values):
    h_url = get_host_from_url_robust(row[0])
    h_top_level = get_host_from_url_robust(row[1])
    h_triggering = get_host_from_url_robust(row[2])
    url = urllib.unquote(row[0])
    found_leak = False
    for value in values:
        if url.find(value) != -1:
            leak = {
                'Destination URL host (leaked to)': h_url,
                'Top level URL host': h_top_level,
                'Trigger URL host (leaker)': h_triggering,
                'Leaked value': value,
                'Destination URL unquoted': url
            }
            #pprint(leak)
            found_leak = True
    if not found_leak:
        # the above is the most basic kind of leak
        # slightly more sophisticated is to look in the headers of the request
        # and post bodies for POST requests
        # I need to do something else to find more sophisticated ones, i.e. if the id being used to track me
        # is not one in the cookie store but is being propagated in thirdparty to thirdparty requests I need to know
        print row






def analyze_cookie_matching():
    rows = conn.execute("SELECT visit_id, baseDomain, name, value, host FROM profile_cookies").fetchall()
    values = set([])
    for row in rows:
        value = row[3]
        values.add(value)
    rows = conn.execute("SELECT url, top_level_url, triggering_origin, req_call_stack, method, post_body FROM http_requests").fetchall()
    for row in rows:
        if row[0] and row[1]:
            h_url = get_host_from_url_robust(row[0])
            h_top_level = get_host_from_url_robust(row[1])
            h_triggering = get_host_from_url_robust(row[2])
            if h_url != h_triggering and h_triggering != h_top_level:
                # here we have one third party making a request to another, let's check what they are leaking
                check_row_for_leakage(row, values)
            elif h_url != h_triggering:
                # here we have first party making a request to third party
                #print '{}\t{}\t{}'.format(h_url, h_top_level, h_triggering)
                pass



if __name__ == "__main__":
    analyze_cookie_matching()