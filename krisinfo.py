#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from threading import Thread
from queue import Queue
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import http.client
import json
import re


def main():
    res = request(Api.URL)
    if res is None:
        print('NO DATA')
        quit()
    json_data = json.loads(res)
    # print(json.dumps(json_data, indent=2, ensure_ascii=False))  # debug
    parsed = parse_data(json_data)
    print_data(parsed)


def parse_data(data):
    parsed = []
    queue = build_queue(data)

    for i in range(queue.qsize()):
        thread = Thread(target=parse_data_thread, args=(queue, parsed))
        thread.daemon = True
        thread.start()

    queue.join()

    return parsed


def build_queue(data):
    queue = Queue()

    for i in data['Entries']:
        date = format_time(i['Updated']).partition(' ')
        title = i['Title']
        summary = i['Summary'].replace("\n", "")
        xml = i['Link']['LinkUrl']

        queue.put((date, title, summary, xml))

    return queue


def parse_data_thread(queue, parsed):
    while not queue.empty():
        q = queue.get()

        data = request(q[3])
        link = parse_xml(data) if data is not None else None
        parsed.append((q[0], q[1], q[2], link))

        queue.task_done()


def parse_xml(data):
    root = ET.fromstring(data)
    namespace = get_namespace(root)
    link = root.findall(".//ns:web", namespace)

    return link


def get_namespace(element):
    match = re.search(r'\{(.*?)\}', element.tag).group(1)

    return {'ns': match} if match else ''


def request(url):
    try:
        return urllib.request.urlopen(url).read().decode('utf-8')

    except urllib.error.HTTPError as e:
        print("HTTPError: {}\n{}".format(e.code, url))
        return None

    except urllib.error.URLError as e:
        print("URLError: {}\n{}".format(e.reason, url))
        return None

    except http.client.HTTPException as e:
        print("HTTPException: {}\n{}".format(e, url))
        return None

    except Exception as e:
        print("Exception: {}\n{}".format(e, url))
        return None


def format_time(time):
    format = '%Y-%m-%dT%H:%M:%S'
    formatted = datetime \
        .strptime(time.partition('+')[0], format) \
        .strftime('%y-%m-%d  %H:%M')

    return formatted


def print_data(parsed):
    if not parsed:
        print('NO DATA')
        quit()

    print()
    for data in sorted(parsed, key=lambda tup: tup[0]):
        print_date(data[0])
        print_title(data[1])
        print_summary(data[2])
        print_link(data[3])
        print()


def print_date(date):
    print(Style.BOLD + Style.green(date[0]) + Style.dim(date[2]))


def print_title(title):
    print(Style.blue(title))


def print_summary(summary):
    print(('\n'.join(line for line in re.findall(
        r'.{1,' + re.escape("80") + '}(?:\s+|$)', summary))))


def print_link(link):
    if link is not None:
        prefix = '\x1b]8;;'
        link = '\a' + 'Läs mer' + prefix + '\a'
        for url in link:
            print(prefix + url.text + link)
    else:
        print(Style.dim('[No link]'))


class Api:
    URL = 'http://api.krisinformation.se/v1/feed?format=json'


class Style:
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    BOLD = "\033[1m"
    DIM = '\033[2m'

    @staticmethod
    def dim(output):
        return Style.DIM + output + Style.DEFAULT

    @staticmethod
    def green(output):
        return Style.GREEN + output + Style.DEFAULT

    @staticmethod
    def blue(output):
        return Style.BLUE + output + Style.DEFAULT


if __name__ == "__main__":
    main()
