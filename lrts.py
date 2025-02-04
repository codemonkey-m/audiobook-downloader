#!/usr/bin/env python3

import requests
import html
import json
import os
import sys
from bs4 import BeautifulSoup
from threading import Thread


def main():
    bookId = sys.argv[1]

    page = 0
    while True:
        if not getSections(bookId, page, 2000):
            break

        page += 1

    print("全部下载完成!")


def getSections(bookId, index=0, totalCount=1):
    folder = str(bookId)
    if not os.path.exists(folder):
        os.makedirs(folder)

    url = f'http://www.lrts.me/ajax/book/{bookId}/{index}/{totalCount}'

    print("开始拉取第%d页数据"%(index+1))
    print(url)
    r = requests.post(url)

    resourceCount = freeCount = foundUrlCount = 0

    fileset = set()
    if r.status_code == 200:
        jsonstr = html.unescape(r.content.decode('utf-8'))
        resources = json.loads(jsonstr)['data']['data']
        if not resources:
            return False

        print('Collecting mp3 links ...')
        for resource in resources:
            resourceCount += 1
            if resource['payType'] == 0:
                freeCount += 1

            u = getFileUrl(bookId, resource['resId'])
            n = resource['resName']
            if u:
                foundUrlCount += 1
                fileset.add((u, n))

    if len(fileset) == 0:
        return False
    
    print(f'Total: {resourceCount}, free: {freeCount}, found: {foundUrlCount}')
    print("开始下载...")

    threads = []
    for mp3Link, mp3Name in fileset:
        t = Thread(target=downloadFile, args=(mp3Link, folder, mp3Name))
        t.start()
        threads.append(t)

    print(f'{len(threads)} threads working')
    for t in threads:
        t.join()

    print('本页下载完成!\n')
    return True


def getFileUrl(bookId, resourceId):
    url = f'http://www.lrts.me/ajax/path/4/{bookId}/{resourceId}'

    r = requests.get(url)
    if r.status_code == 200:
        jsonstr = html.unescape(r.content.decode('utf-8'))
        u = json.loads(jsonstr)['data']
        return u


def downloadFile(url, folder, fileName, ext='.mp3'):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(f'{folder}/{fileName}{ext}', 'wb') as f:
                f.write(r.content)
    except:
        downloadFile(url, folder, fileName)


def getPlayList(resourceType, resourceId, sections='', flow=''):
    url = f'http://www.lrts.me/ajax/playlist/{resourceType}/{resourceId}'

    if sections:
        url += '/' + sections
    if flow:
        url += '/' + flow

    print(url)

    result = []
    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, 'html.parser')

        for li in soup.select('li.section-item'):
            print(li)
            mp3Link = li.find('input', {'name': 'source'}).get('value')
            mp3Name = li.find('input', {'name': 'player-r-name'}).get('value')

            result.append((mp3Link, mp3Name))

    return result


if __name__ == '__main__':
    main()

