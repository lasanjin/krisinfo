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
        if data is not None:
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
    except Exception as e:
        print("Exception: %s" % e)
        return None


def format_time(time):
    format = '%Y-%m-%dT%H:%M:%S'
    formatted = datetime \
        .strptime(time.partition('+')[0], format) \
        .strftime('%y-%m-%d  %H:%M')

    return formatted


class Api:
    URL = 'http://api.krisinformation.se/v1/feed?format=json'


class Style:
    DEFAULT = '\033[0m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    BOLD = "\033[1m"
    DIM = '\033[2m'

    @staticmethod
    def style(output, color, styles=[]):
        if color is not None:
            output = {
                'green': Style.GREEN + '%s',
                'blue': Style.BLUE + '%s',
            }[color] % output

        for style in styles:
            output = {
                'bold': Style.BOLD + '%s',
                'dim': Style.DIM + '%s'
            }[style] % output

        return output + Style.DEFAULT


# -----------------------------------------------------------------
# PRINT
# -----------------------------------------------------------------
def print_data(parsed):
    if not parsed:
        print('NO DATA')
        quit()

    print()
    for data in sorted(parsed, key=lambda tup: tup[0]):
        # print date
        print(Style.style(data[0][0], 'green', ['bold']) +
              Style.style(data[0][2], None, ['dim']))
        # print title
        print(Style.style(data[1], 'blue'))
        # print summary
        print(('\n'.join(line for line in re.findall(
            r'.{1,' + re.escape("80") + '}(?:\s+|$)', data[2]))))
        # print link
        if data[3] is not None:
            prefix = '\x1b]8;;'
            hlink = '\a' + 'Läs mer' + prefix + '\a'
            for url in data[3]:
                print(prefix + url.text + hlink)
        else:
            print(Style.style('[NO LINK]', None, ['dim']))
        print()


if __name__ == "__main__":
    main()
