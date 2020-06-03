#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function  # print python2
import xml.etree.ElementTree as ET
from datetime import datetime
from threading import Thread
import json
import re
import six

if six.PY2:  # python2
    from Queue import Queue
    import urllib2
    import httplib
elif six.PY3:  # python3
    from queue import Queue
    import http.client as httplib  # httplib.HTTPException
    import urllib.error as urllib2  # urllib2.HTTPError
    import urllib.request


def main():
    data = get_data()
    mapped = map_data(data)
    print_data(mapped)


def get_data():
    url = api.URL
    res = request(url)
    json_data = json.loads(res)

    return json_data


def map_data(data):
    mapped = []
    queue = build_queue(data)

    for i in range(queue.qsize()):
        thread = Thread(target=map_data_thread,
                        args=(queue, mapped))
        thread.daemon = True
        thread.start()

    queue.join()

    return mapped


def build_queue(data):
    queue = Queue()

    for i in data['Entries']:
        date = format_time(i['Updated']).partition(' ')
        title = i['Title']
        summary = i['Summary'].replace("\n", "")
        xml = i['Link']['LinkUrl']

        queue.put((date, title, summary, xml))

    return queue


def map_data_thread(queue, mapped):
    while not queue.empty():
        q = queue.get()

        data = request(q[3])
        link = parse_xml(data)
        mapped.append((q[0], q[1], q[2], link))

        queue.task_done()


def parse_xml(data):
    root = ET.fromstring(data)
    namespace = get_namespace(root)
    link = root.findall(".//ns:web", namespace)

    return link


def get_namespace(element):
    match = re.search(r'\{(.*?)\}', element.tag).group(1)

    return {'ns': match} if match else ''


# -----------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------
def request(url):
    try:
        if six.PY2:
            return urllib2.urlopen(url).read()
        elif six.PY3:
            return urllib.request.urlopen(url).read().decode('utf-8')

    except urllib2.HTTPError as e:
        print("HTTPError: {}".format(e.code))

    except urllib2.URLError as e:
        print("URLError: {}".format(e.reason))

    except httplib.HTTPException as e:
        print("HTTPException: {}".format(e))

    except Exception as e:
        print("Exception: {}".format(e))


def format_time(time):
    format = '%Y-%m-%dT%H:%M:%S'
    formatted = datetime \
        .strptime(time.partition('+')[0], format) \
        .strftime('%y-%m-%d  %H:%M')

    return formatted


# -----------------------------------------------------------------
# PRINT
# -----------------------------------------------------------------
def print_data(mapped):
    if not mapped:
        print('NO DATA')
        quit()

    print()
    for data in sorted(mapped, key=lambda tup: tup[0]):
        print_date(data[0])
        print_title(data[1])
        print_summary(data[2])
        print_link(data[3])
        print()


def print_date(date):
    print(color.BOLD + color.green(date[0]) + color.dim(date[2]))


def print_title(title):
    print(color.blue(title))


def print_summary(summary):
    print(('\n'.join(line for line in re.findall(
        r'.{1,' + re.escape("80") + '}(?:\s+|$)', summary))))


def print_link(link):
    for url in link:
        print(const.PREFIX + url.text + const.TEXT('Läs mer'))


# -----------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------
class api:
    URL = 'http://api.krisinformation.se/v1/feed?format=json'


class const:
    PREFIX = '\x1b]8;;'

    @staticmethod
    def TEXT(text):
        return '\a' + text + const.PREFIX + '\a'


class color:
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    BOLD = "\033[1m"
    DIM = '\033[2m'

    @staticmethod
    def dim(output):
        return color.DIM + output + color.DEFAULT

    @staticmethod
    def green(output):
        return color.GREEN + output + color.DEFAULT

    @staticmethod
    def blue(output):
        return color.BLUE + output + color.DEFAULT


if __name__ == "__main__":
    main()
