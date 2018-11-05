from __future__ import absolute_import
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from hashlib import md5
from glob import glob
from PIL import Image
import traceback
import random
import json
import traceback
import urllib
import sys
import gzip
import os
import pandas as pd
import time
from adblockparser import AdblockRules
import os

from ..SocketInterface import clientsocket
from ..MPLogger import loggingclient
from .utils.lso import get_flash_cookies
from .utils.firefox_profile import get_cookies
from .utils.webdriver_extensions import (scroll_down,
                                         wait_until_loaded,
                                         get_intra_links,
                                         execute_in_all_frames,
                                         execute_script_with_retry,
                                         move_to_and_click)
from selenium.webdriver.common.by import By
from six.moves import range
import six
from urlparse import urlparse, urljoin
import csv

# Constants for bot mitigation
NUM_MOUSE_MOVES = 10  # Times to randomly move the mouse
RANDOM_SLEEP_LOW = 1  # low (in sec) for random sleep between page loads
RANDOM_SLEEP_HIGH = 7  # high (in sec) for random sleep between page loads
RULE_FILE = 'easylist.txt'


def bot_mitigation(webdriver):
    """ performs three optional commands for bot-detection
	mitigation when getting a site """

    # bot mitigation 1: move the randomly around a number of times
    window_size = webdriver.get_window_size()
    num_moves = 0
    num_fails = 0
    while num_moves < NUM_MOUSE_MOVES + 1 and num_fails < NUM_MOUSE_MOVES:
        try:
            if num_moves == 0:  # move to the center of the screen
                x = int(round(window_size['height'] / 2))
                y = int(round(window_size['width'] / 2))
            else:  # move a random amount in some direction
                move_max = random.randint(0, 500)
                x = random.randint(-move_max, move_max)
                y = random.randint(-move_max, move_max)
            action = ActionChains(webdriver)
            action.move_by_offset(x, y)
            action.perform()
            num_moves += 1
        except MoveTargetOutOfBoundsException:
            num_fails += 1
            pass

    # bot mitigation 2: scroll in random intervals down page
    scroll_down(webdriver)

    # bot mitigation 3: randomly wait so page visits happen with irregularity
    time.sleep(random.randrange(RANDOM_SLEEP_LOW, RANDOM_SLEEP_HIGH))


def login_colo(webdriver):
    iam = 'barber5@illinois.edu'
    p = 'oKN6$mGk&qGb'
    login_element = webdriver.find_element_by_class_name("js-login-button")
    move_to_and_click(webdriver, login_element)
    uname_element = webdriver.find_element_by_name("email")
    uname_element.send_keys(iam)
    pw_element = webdriver.find_element_by_name("passwrd")
    pw_element.send_keys(p)
    submit_element = webdriver.find_element_by_class_name("js-send")
    move_to_and_click(webdriver, submit_element)
    time.sleep(random.random() * 4 + 5.0)


def process_duke_directory(webdriver, manager_params):
    sock = clientsocket()

    sock.connect(*manager_params['aggregator_address'])
    create_table_query = ("""
			CREATE TABLE IF NOT EXISTS ads_found (
			  img_source TEXT UNIQUE,
			  table_dict TEXT
			)
			""", ())
    sock.send(create_table_query)

    create_table_query = ("""
				CREATE TABLE IF NOT EXISTS pages_found (
				  url TEXT UNIQUE,
				  visited INTEGER DEFAULT 0,
				  meta TEXT
				)
				""", ())
    sock.send(create_table_query)

    insert_query_string = """
				INSERT INTO pages_found (url, visited)
				VALUES (?, ?)
				"""
    listings = webdriver.find_elements_by_class_name("document")
    for listing_element in listings:
        try:
            a_element = listing_element.find_element_by_tag_name("a")
            url = a_element.get_attribute("href")
            if url.find("active_fedora") != -1:
                continue
            sock.send((insert_query_string, (url, 0)))
        except NoSuchElementException as e:
            tb = traceback.format_exc()
            print tb
    sock.close()


def process_reddit(webdriver, manager_params, browser_params):
    links = webdriver.find_elements_by_tag_name("a")
    linklist = []
    exclude = ['imgur', 'reddit', 'redd.it', 'twitter', 'img', 'gfycat', 'streamable']
    for link in links:

        if ("title" in link.get_attribute("class") and not (any(x in link.get_attribute("href") for x in exclude))):
            linklist.append(link.get_attribute("href"))
        else:
            continue
    path = 'sublinks/'
    sub = webdriver.current_url.split('/')[4]
    if sub + '.csv' in os.listdir(path):
        with open(path + sub + '.csv', 'a') as csvfile:
            csvwriter = csv.writer(csvfile)
            for link in linklist:
                print(link)
                csvwriter.writerow([link])
    else:
        with open(path + sub + '.csv', 'wb') as csvfile:
            csvwriter = csv.writer(csvfile)
            for link in linklist:
                print(link)
                csvwriter.writerow([link])

def process_google(webdriver, manager_params, browser_params, t):
    links = webdriver.find_elements_by_tag_name('a')
    exclude = ['google', "/search", "imdb","hbo","youtube"]
    linklist = []
    for link in links:
        if(link.get_attribute("href") == None):
            continue
        if ('https' in link.get_attribute("href") and not (any(x in link.get_attribute("href") for x in exclude))):
            linklist.append(link.get_attribute("href"))
    path = 'googlinks/'

    if t + '.csv' in os.listdir(path):
        with open(path + t+ '.csv', 'a') as csvfile:
            csvwriter = csv.writer(csvfile)
            for link in linklist:
                csvwriter.writerow([link])
    else:
        with open(path + t + '.csv', 'wb') as csvfile:
            csvwriter = csv.writer(csvfile)
            for link in linklist:
                csvwriter.writerow([link])

def google_login(webdriver):
    webdriver.get("https://accounts.google.com")
    time.sleep(2)
    emailid = webdriver.find_element_by_name("identifier")
    emailid.send_keys("scrapetest1@gmail.com")

    enext = webdriver.find_element_by_id("identifierNext")
    enext.click()
    time.sleep(2)
    passw = webdriver.find_element_by_name("password")
    passw.send_keys("testingacc1")
    time.sleep(2)

    signin = webdriver.find_element_by_id("passwordNext")
    signin.click()
    time.sleep(2)


def visit_sites(webdriver, slist):
    webdriver.get("https://accounts.google.com")
    time.sleep(4)
    for site in slist:
        exclude = ['media', 'download']
        if all(x not in site for x in exclude):
            webdriver.get(site)
    webdriver.get("https://accounts.google.com")


def clear_google(webdriver):
    webdriver.get("https://myactivity.google.com")
    time.sleep(1)
    dels = webdriver.find_elements_by_partial_link_text("Delete activity by")
    del1 = dels[len(dels) - 1]
    del1.click()
    time.sleep(2)
    divs = webdriver.find_elements_by_class_name('md-text')
    for div in divs:
        if div.text == 'Today':
            div.click()
    divs = webdriver.find_elements_by_class_name('md-text')
    for div in divs:
        if div.text == 'All time':
            div.click()
    buttons = webdriver.find_elements_by_tag_name('button')
    # buttons[1].click()
    time.sleep(1)
    buttons[2].click()
    buttons = webdriver.find_elements_by_tag_name('button')
    print(len(buttons))

    buttons[4].click()


def process_duke_page(webdriver, manager_params, browser_params):
    download_menu = webdriver.find_element_by_id("download-menu")
    a_elements = download_menu.find_elements_by_tag_name("a")
    if not os.path.exists("images/ad-archive/duke/"):
        os.makedirs("images/ad-archive/duke/")
    for a_element in a_elements:
        url = a_element.get_attribute("href")
        if url.find("full/full") != -1:
            # found the image
            urllib.urlretrieve(url, "images/ad-archive/duke/" + url.split('/')[-5])

    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])
    update_query_string = """
				UPDATE pages_found SET visited=1, meta=?
				WHERE url=?
				"""
    meta_dict = {}
    item_info = webdriver.find_element_by_id("item-info")
    dt_list = item_info.find_elements_by_tag_name("dt")
    dd_list = item_info.find_elements_by_tag_name("dd")
    for i in range(len(dt_list)):
        current_dt = dt_list[i]
        current_dd = dd_list[i]
        dt_text = current_dt.text[:-1]
        dd_text = current_dd.text
        meta_dict[dt_text] = dd_text
    sock.send((update_query_string, (json.dumps(meta_dict), webdriver.current_url)))
    sock.close()


def get_element_text(element):
    text_so_far = ""
    element_stack = []
    element_stack.append(element)
    while len(element_stack) > 0:
        next_element = element_stack.pop()
        text_so_far += text_so_far + next_element.text
        next_children = next_element.find_elements_by_css_selector("*")
        for next_child in next_children:
            element_stack.append(next_child)
    return text_so_far


def process_colo(webdriver, manager_params):
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])
    create_table_query = ("""
		CREATE TABLE IF NOT EXISTS ads_found (
		  img_source TEXT UNIQUE,
		  table_dict TEXT
		)
		""", ())
    sock.send(create_table_query)

    insert_query_string = """
			INSERT INTO ads_found (img_source, table_dict)
			VALUES (?, ?)
			"""
    listings = webdriver.find_elements_by_class_name("listing")
    for listing_element in listings:
        try:
            move_to_and_click(webdriver, listing_element)
            img_element = webdriver.find_element_by_class_name("single-media-current-pic")
            img_src = img_element.get_attribute("src")
            urllib.urlretrieve(img_src, "images/ad-archive/" + img_src.split('/')[-1])
            table_element = webdriver.find_element_by_class_name("single-table")
            rows = table_element.find_elements_by_tag_name("tr")
            table_dict = {}
            for row in rows:
                if row.text.find("Industry") == 0:
                    table_dict['Industry'] = row.text[8:].split(",")
                if row.text.find("Media") == 0:
                    table_dict["Media"] = row.text[5:].split(",")
                if row.text.find("Market") == 0:
                    table_dict["Market"] = row.text[6:].split(",")
                if row.text.find("Released") == 0:
                    table_dict["Released"] = row.text[8:]
            table_str = json.dumps(table_dict)
            sock.send((insert_query_string, (img_src, table_str)))

            time.sleep(random.random() * 8.0 + 3.0)
        except NoSuchElementException as e:
            tb = traceback.format_exc()
            print tb
    time.sleep(random.random() * 5 + 5)
    sock.close()


def close_other_windows(webdriver):
    """
	close all open pop-up windows and tabs other than the current one
	"""
    main_handle = webdriver.current_window_handle
    windows = webdriver.window_handles
    if len(windows) > 1:
        for window in windows:
            if window != main_handle:
                webdriver.switch_to_window(window)
                webdriver.close()
        webdriver.switch_to_window(main_handle)


def tab_restart_browser(webdriver):
    """
	kills the current tab and creates a new one to stop traffic
	"""
    # note: this technically uses windows, not tabs, due to problems with
    # chrome-targeted keyboard commands in Selenium 3 (intermittent
    # nonsense WebDriverExceptions are thrown). windows can be reliably
    # created, although we do have to detour into JS to do it.
    close_other_windows(webdriver)

    if webdriver.current_url.lower() == 'about:blank':
        return

    # Create a new window.  Note that it is not practical to use
    # noopener here, as we would then be forced to specify a bunch of
    # other "features" that we don't know whether they are on or off.
    # Closing the old window will kill the opener anyway.
    webdriver.execute_script("window.open('')")

    # This closes the _old_ window, and does _not_ switch to the new one.
    webdriver.close()

    # The only remaining window handle will be for the new window;
    # switch to it.
    assert len(webdriver.window_handles) == 1
    webdriver.switch_to_window(webdriver.window_handles[0])


def get_website(url, sleep, visit_id, webdriver,
                browser_params, extension_socket):
    """
	goes to <url> using the given <webdriver> instance
	"""

    tab_restart_browser(webdriver)

    if extension_socket is not None:
        extension_socket.send(visit_id)

    # Execute a get through selenium
    try:
        webdriver.get(url)
    except TimeoutException:
        pass

    # Sleep after get returns
    time.sleep(sleep)

    # Close modal dialog if exists
    try:
        WebDriverWait(webdriver, .5).until(EC.alert_is_present())
        alert = webdriver.switch_to_alert()
        alert.dismiss()
        time.sleep(1)
    except TimeoutException:
        pass

    close_other_windows(webdriver)

    if browser_params['bot_mitigation']:
        bot_mitigation(webdriver)


def extract_links(webdriver, browser_params, manager_params):
    link_elements = webdriver.find_elements_by_tag_name('a')
    link_urls = set(element.get_attribute("href") for element in link_elements)

    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])
    create_table_query = ("""
	CREATE TABLE IF NOT EXISTS links_found (
	  found_on TEXT,
	  location TEXT
	)
	""", ())
    sock.send(create_table_query)

    if len(link_urls) > 0:
        current_url = webdriver.current_url
        insert_query_string = """
		INSERT INTO links_found (found_on, location)
		VALUES (?, ?)
		"""
        for link in link_urls:
            sock.send((insert_query_string, (current_url, link)))

    sock.close()


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
    rules = AdblockRules(ruletext)
    return rules


def extract_iframes(webdriver, visit_id, browser_params, manager_params):
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])
    create_table_query = ("""
	CREATE TABLE IF NOT EXISTS iframes_found (
	  visit_id INTEGER,
	  found_on TEXT,
	  location TEXT,
	  frame_id TEXT,
	  element_attrs TEXT,
	  inner_html TEXT

	)
	""", ())
    sock.send(create_table_query)

    webdriver.set_window_size(3000, 800)

    iframe_elements = webdriver.find_elements_by_tag_name('iframe')
    iframe_urls = set([])
    iframe_dict = {}
    current_url = webdriver.current_url
    host = urlparse(current_url).hostname
    screenshots_path = '{}/iframes'.format(manager_params['screenshot_path'])
    if not os.path.exists(screenshots_path):
        os.makedirs(screenshots_path)
    host_path = '{}/{}'.format(screenshots_path, host)
    if not os.path.exists(host_path):
        os.makedirs(host_path)

    for count, element in enumerate(iframe_elements):
        element_src = element.get_attribute("src")
        file_prefix = ''
        element_png = element.screenshot_as_png
        if os.path.isfile('{}/{}.png'.format(host_path, element.id)):
            print 'woah file {} already exists'.format(element.id)

        with open('{}/{}.png'.format(host_path, element.id), 'wb') as fi:
            fi.write(element_png)
        attrs = webdriver.execute_script(
            'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;',
            element)
        inner_html = webdriver.execute_script("return arguments[0].innerHTML;", element)

        insert_query_string = """
		INSERT INTO iframes_found (visit_id, found_on, location, frame_id, element_attrs, inner_html)
		VALUES (?, ?, ?, ?, ?, ?)
		"""

        sock.send(
            (insert_query_string, (visit_id, current_url, element_src, element.id, str(attrs), inner_html)))

    sock.close()


def recursive_iframes(webdriver, browser_params, manager_params, depth=0, parent_iframe=None):
    print 'iframe depth {}'.format(depth)
    iframe_elements = webdriver.find_elements_by_tag_name('iframe')
    for element in iframe_elements:
        webdriver.switch_to.frame(element)
        recursive_iframes(webdriver, browser_params, manager_params, depth + 1)

    if parent_iframe:
        webdriver.switch_to.frame(parent_iframe)
        print 'switched back to my parent'


def browse_website(url, num_links, sleep, visit_id, webdriver,
                   browser_params, manager_params, extension_socket):
    """Calls get_website before visiting <num_links> present on the page.

	Note: the site_url in the site_visits table for the links visited will
	be the site_url of the original page and NOT the url of the links visited.
	"""
    # First get the site
    get_website(url, sleep, visit_id, webdriver,
                browser_params, extension_socket)

    # Connect to logger
    logger = loggingclient(*manager_params['logger_address'])

    # Then visit a few subpages
    for i in range(num_links):
        links = [x for x in get_intra_links(webdriver, url)
                 if x.is_displayed() is True]
        if not links:
            break
        r = int(random.random() * len(links))
        logger.info("BROWSER %i: visiting internal link %s" % (
            browser_params['crawl_id'], links[r].get_attribute("href")))

        try:
            links[r].click()
            wait_until_loaded(webdriver, 300)
            time.sleep(max(1, sleep))
            if browser_params['bot_mitigation']:
                bot_mitigation(webdriver)
            webdriver.back()
            wait_until_loaded(webdriver, 300)
        except Exception:
            pass


def dump_flash_cookies(start_time, visit_id, webdriver, browser_params,
                       manager_params):
    """ Save newly changed Flash LSOs to database

	We determine which LSOs to save by the `start_time` timestamp.
	This timestamp should be taken prior to calling the `get` for
	which creates these changes.
	"""
    # Set up a connection to DataAggregator
    tab_restart_browser(webdriver)  # kills window to avoid stray requests
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])

    # Flash cookies
    flash_cookies = get_flash_cookies(start_time)
    for cookie in flash_cookies:
        query = ("INSERT INTO flash_cookies (crawl_id, visit_id, domain, "
                 "filename, local_path, key, content) VALUES (?,?,?,?,?,?,?)",
                 (browser_params['crawl_id'], visit_id, cookie.domain,
                  cookie.filename, cookie.local_path, cookie.key,
                  cookie.content))
        sock.send(query)

    # Close connection to db
    sock.close()


def dump_profile_cookies(start_time, visit_id, webdriver,
                         browser_params, manager_params):
    """ Save changes to Firefox's cookies.sqlite to database

	We determine which cookies to save by the `start_time` timestamp.
	This timestamp should be taken prior to calling the `get` for
	which creates these changes.

	Note that the extension's cookieInstrument is preferred to this approach,
	as this is likely to miss changes still present in the sqlite `wal` files.
	This will likely be removed in a future version.
	"""
    # Set up a connection to DataAggregator
    tab_restart_browser(webdriver)  # kills window to avoid stray requests
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])

    # Cookies
    rows = get_cookies(browser_params['profile_path'], start_time)
    if rows is not None:
        for row in rows:
            query = ("INSERT INTO profile_cookies (crawl_id, visit_id, "
                     "baseDomain, name, value, host, path, expiry, accessed, "
                     "creationTime, isSecure, isHttpOnly) VALUES "
                     "(?,?,?,?,?,?,?,?,?,?,?,?)", (browser_params['crawl_id'],
                                                   visit_id) + row)
            sock.send(query)

    # Close connection to db
    sock.close()


def save_screenshot(visit_id, crawl_id, driver, manager_params, suffix=''):
    """ Save a screenshot of the current viewport"""
    if suffix != '':
        suffix = '-' + suffix

    urlhash = md5(driver.current_url.encode('utf-8')).hexdigest()
    outname = os.path.join(manager_params['screenshot_path'],
                           '%i-%s%s.png' %
                           (visit_id, urlhash, suffix))
    driver.save_screenshot(outname)


def _stitch_screenshot_parts(visit_id, crawl_id, logger, manager_params):
    # Read image parts and compute dimensions of output image
    total_height = -1
    max_scroll = -1
    max_width = -1
    images = dict()
    parts = list()
    for f in glob(os.path.join(manager_params['screenshot_path'],
                               'parts',
                               '%i*-part-*.png' % visit_id)):

        # Load image from disk and parse params out of filename
        img_obj = Image.open(f)
        width, height = img_obj.size
        parts.append((f, width, height))
        outname, _, index, curr_scroll = os.path.basename(f).rsplit('-', 3)
        curr_scroll = int(curr_scroll.split('.')[0])
        index = int(index)

        # Update output image size
        if curr_scroll > max_scroll:
            max_scroll = curr_scroll
            total_height = max_scroll + height

        if width > max_width:
            max_width = width

        # Save image parameters
        img = {}
        img['object'] = img_obj
        img['scroll'] = curr_scroll
        images[index] = img

    # Output filename same for all parts, so we can just use last filename
    outname = outname + '.png'
    outname = os.path.join(manager_params['screenshot_path'], outname)
    output = Image.new('RGB', (max_width, total_height))

    # Compute dimensions for output image
    for i in range(max(images.keys()) + 1):
        img = images[i]
        output.paste(im=img['object'], box=(0, img['scroll']))
        img['object'].close()
    try:
        output.save(outname)
    except SystemError:
        logger.error(
            "BROWSER %i: SystemError while trying to save screenshot %s. \n"
            "Slices of image %s \n Final size %s, %s." %
            (crawl_id, outname, '\n'.join([str(x) for x in parts]),
             max_width, total_height)
        )
        pass


def screenshot_full_page(visit_id, crawl_id, driver, manager_params,
                         suffix=''):
    logger = loggingclient(*manager_params['logger_address'])

    outdir = os.path.join(manager_params['screenshot_path'], 'parts')
    if not os.path.isdir(outdir):
        os.mkdir(outdir)
    if suffix != '':
        suffix = '-' + suffix
    urlhash = md5(driver.current_url.encode('utf-8')).hexdigest()
    outname = os.path.join(outdir, '%i-%s%s-part-%%i-%%i.png' %
                           (visit_id, urlhash, suffix))

    try:
        part = 0
        max_height = execute_script_with_retry(
            driver, 'return document.body.scrollHeight;')
        inner_height = execute_script_with_retry(
            driver, 'return window.innerHeight;')
        curr_scrollY = execute_script_with_retry(
            driver, 'return window.scrollY;')
        prev_scrollY = -1
        driver.save_screenshot(outname % (part, curr_scrollY))
        while ((curr_scrollY + inner_height) < max_height
               and curr_scrollY != prev_scrollY):

            # Scroll down to bottom of previous viewport
            try:
                driver.execute_script('window.scrollBy(0, window.innerHeight)')
            except WebDriverException:
                logger.info(
                    "BROWSER %i: WebDriverException while scrolling, "
                    "screenshot may be misaligned!" % crawl_id)
                pass

            # Update control variables
            part += 1
            prev_scrollY = curr_scrollY
            curr_scrollY = execute_script_with_retry(
                driver, 'return window.scrollY;')

            # Save screenshot
            driver.save_screenshot(outname % (part, curr_scrollY))
    except WebDriverException:
        excp = traceback.format_exception(*sys.exc_info())
        logger.error(
            "BROWSER %i: Exception while taking full page screenshot \n %s" %
            (crawl_id, ''.join(excp)))
        return

    _stitch_screenshot_parts(visit_id, crawl_id, logger, manager_params)


def dump_page_source(visit_id, driver, manager_params, suffix=''):
    if suffix != '':
        suffix = '-' + suffix

    outname = md5(driver.current_url.encode('utf-8')).hexdigest()
    outfile = os.path.join(manager_params['source_dump_path'],
                           '%i-%s%s.html' % (visit_id, outname, suffix))

    with open(outfile, 'wb') as f:
        f.write(driver.page_source.encode('utf8'))
        f.write(b'\n')


def recursive_dump_page_source(visit_id, driver, manager_params, suffix=''):
    """Dump a compressed html tree for the current page visit"""
    if suffix != '':
        suffix = '-' + suffix

    outname = md5(driver.current_url.encode('utf-8')).hexdigest()
    outfile = os.path.join(manager_params['source_dump_path'],
                           '%i-%s%s.json.gz' % (visit_id, outname, suffix))

    def collect_source(driver, frame_stack, rv={}):
        is_top_frame = len(frame_stack) == 1

        # Gather frame information
        doc_url = driver.execute_script("return window.document.URL;")
        if is_top_frame:
            page_source = rv
        else:
            page_source = dict()
        page_source['doc_url'] = doc_url
        source = driver.page_source
        if type(source) != six.text_type:
            source = six.text_type(source, 'utf-8')
        page_source['source'] = source
        page_source['iframes'] = dict()

        # Store frame info in correct area of return value
        if is_top_frame:
            return
        out_dict = rv['iframes']
        for frame in frame_stack[1:-1]:
            out_dict = out_dict[frame.id]['iframes']
        out_dict[frame_stack[-1].id] = page_source

    page_source = dict()
    execute_in_all_frames(driver, collect_source, {'rv': page_source})

    with gzip.GzipFile(outfile, 'wb') as f:
        f.write(json.dumps(page_source).encode('utf-8'))


def recursive_dump_page_source_to_db(visit_id, driver, manager_params):
    def collect_source(driver, frame_stack, rv={}):
        is_top_frame = len(frame_stack) == 1

        # Gather frame information
        doc_url = driver.execute_script("return window.document.URL;")
        if is_top_frame:
            page_source = rv
        else:
            page_source = dict()
        page_source['doc_url'] = doc_url
        source = driver.page_source
        if type(source) != six.text_type:
            source = six.text_type(source, 'utf-8')
        page_source['source'] = source
        page_source['iframes'] = dict()

        # Store frame info in correct area of return value
        if is_top_frame:
            return
        out_dict = rv['iframes']
        for frame in frame_stack[1:-1]:
            out_dict = out_dict[frame.id]['iframes']
        out_dict[frame_stack[-1].id] = page_source

    page_source = dict()
    execute_in_all_frames(driver, collect_source, {'rv': page_source})

    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])
    create_table_query = ("""
	CREATE TABLE IF NOT EXISTS recursive_source (
	  visit_id INTEGER,
	  source TEXT
	)
	""", ())
    sock.send(create_table_query)

    insert_query_string = """
		INSERT INTO recursive_source (visit_id, source)
		VALUES (?, ?)
		"""
    source_json = json.dumps(page_source).encode('utf-8')
    sock.send((insert_query_string, (visit_id, source_json)))

    sock.close()


def get_images_recursively(driver, browser_params, manager_params):
    def print_and_gather_images(driver, frame_stack, print_prefix='', sources=[]):
        elems = driver.find_elements_by_tag_name('img')
        for elem in elems:
            attrs = driver.execute_script(
                'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index) { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value }; return items;',
                elem)
            src = elem.get_attribute('src')
            if src:
                print print_prefix + src
                sources.append(src)

    all_sources = list()
    execute_in_all_frames(driver, print_and_gather_images, {'print_prefix': 'Src ', 'sources': all_sources})
    print "All image sources on page (including all iframes):"
    print all_sources


def get_ad_images_recursively(adblock, visit_id, webdriver, browser_params, manager_params):
    def analyze_frame(driver, frame_stack, adblock=None):
        if len(frame_stack) == 1:
            return
        # just a hack for now, we could miss ads this way if they have an innocuous url inside of a detectable
        # iframe of script source
        img_list = driver.find_elements_by_tag_name('img')
        for img in img_list:
            img_src = img.get_attribute('src')
            #print img_src
            if img_src and adblock.should_block(img_src):
                print 'ad_img_src: {}'.format(img_src)
                # get this image that adblock thinks we should block
                current_url = webdriver.current_url
                screenshots_path = '{}/images'.format(manager_params['screenshot_path'])
                if not os.path.exists(screenshots_path):
                    os.makedirs(screenshots_path)
                '''
                host = urlparse(current_url).hostname
                host_path = '{}/{}'.format(screenshots_path, host)
                if not os.path.exists(host_path):
                    os.makedirs(host_path)
                '''
                img_url = urljoin(current_url, img_src)
                img_file = urlparse(img_url).path.split('/')[-1]
                if os.path.exists('{}/{}'.format(screenshots_path, img_file)):
                    # print 'oops, file already exists: {}'.format(img_file)
                    pass
                else:
                    urllib.urlretrieve(img_url, "{}/{}".format(screenshots_path, img_file))
                sock = clientsocket()
                sock.connect(*manager_params['aggregator_address'])
                create_table_query = ("""
                	CREATE TABLE IF NOT EXISTS ad_images (
                	  visit_id INTEGER,
                	  file_name TEXT
                	)
                	""", ())
                sock.send(create_table_query)

                insert_query_string = """
                		INSERT INTO ad_images (visit_id, file_name)
                		VALUES (?, ?)
                		"""

                sock.send((insert_query_string, (visit_id, img_file)))
                sock.close()
                # return

    current_url = webdriver.current_url
    host = urlparse(current_url).hostname
    screenshots_path = '{}/iframes'.format(manager_params['screenshot_path'])
    if not os.path.exists(screenshots_path):
        os.makedirs(screenshots_path)
    host_path = '{}/{}'.format(screenshots_path, host)
    if not os.path.exists(host_path):
        os.makedirs(host_path)
    execute_in_all_frames(webdriver, analyze_frame, {'adblock': adblock})
