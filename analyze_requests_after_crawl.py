import sqlite3
import urllib
from urlparse import urlparse, parse_qs
from pprint import pprint

DB_FILE = "../crawl_data/crawl-data.sqlite"
conn = sqlite3.connect(DB_FILE)


def get_host_from_url_robust(url):
    # krxd occasionally tries to load a page http://tag/blah

    if url == '[System Principal]':
        return "__sp"

    url_array = urlparse(url).hostname.split('.')
    if len(url_array) < 2:
        return urlparse(url).hostname
    return url_array[-2]


def check_row_for_leakage(row, values, value_dict):
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

                'Destination URL unquoted': url,
                'value_dict': value_dict[value]
            }
            if value_dict[value]['baseDomain'] != 'krxd.net':
                pprint(leak)

            found_leak = True
    if not found_leak:
        # the above is the most basic kind of leak
        # slightly more sophisticated is to look in the headers of the request
        # and post bodies for POST requests
        # I need to do something else to find more sophisticated ones, i.e. if the id being used to track me
        # is not one in the cookie store but is being propagated in thirdparty to thirdparty requests I need to know

        #print row
        pass






def analyze_cookie_matching():

    value_dict = {}

    rows = conn.execute("SELECT visit_id, baseDomain, name, value, host FROM profile_cookies").fetchall()
    values = set([])
    for row in rows:
        value = row[3]

        if len(value) > 3 and value != 'null' and value != 'true':
            values.add(value)
            value_dict[value] = {
                'baseDomain': row[1],
                'name': row[2],
                'host': row[4]
            }

    rows = conn.execute("SELECT url, top_level_url, triggering_origin, req_call_stack, method, post_body FROM http_requests").fetchall()
    for row in rows:
        if row[0] and row[1]:
            h_url = get_host_from_url_robust(row[0])
            h_top_level = get_host_from_url_robust(row[1])
            h_triggering = get_host_from_url_robust(row[2])
            if h_url != h_triggering and h_triggering != h_top_level:
                # here we have one third party making a request to another, let's check what they are leaking

                check_row_for_leakage(row, values, value_dict)
            elif h_url != h_triggering:
                # here we have first party making a request to third party
                pass

def get_all_request_params():
    rows = conn.execute("SELECT url, top_level_url, triggering_origin, req_call_stack, method, post_body, visit_id FROM http_requests").fetchall()
    for row in rows:
        q = urlparse(row[0]).query
        pq = parse_qs(q)
        if len(pq) > 0 and 'google_gid' in pq:
            print row[-1]
            print pq['google_gid']


if __name__ == "__main__":
    get_all_request_params()
