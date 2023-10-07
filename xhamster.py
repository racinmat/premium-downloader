# https://gist.github.com/mopemope/891774
from os import path
from werkzeug import secure_filename
import eventlet
from eventlet.green import urllib2
from pyquery import PyQuery as pq
from urlparse import urlparse
import psyco

psyco.full()

search_urls = [
    "http://xhamster.com/channels/new-asian-%s.html",
]

detail_urls = []

id_mode = True

save_path = "/home/ma2/Public/xhamster/"
pool = eventlet.GreenPool(2)
q = []

import re

base_url = "http://www.xhamster.com"
download_re = re.compile("'file':\s*'([\w\d\.:/_\-\?=]*)'", re.M)
download_re2 = re.compile("'srv':\s*'([\w\d.:/_]*)", re.M)


def get_pagelist(url, page=1):
    q = []
    conn = urllib2.urlopen(url % page)
    page = conn.read()
    d = pq(page)
    for anchor in d("a"):
        href = pq(anchor).attr.href
        if href.startswith("/movies"):
            q.append(base_url + href)
    return q


def get_download_url(url):
    conn = urllib2.urlopen(url)
    page = conn.read()
    file_match = download_re.search(page)
    srv_match = download_re2.search(page)
    if srv_match and file_match:
        file_name = file_match.group(1)
        srv = srv_match.group(1)
        download_url = "%s/flv2/%s" % (srv, file_name)
        file_name = path.basename(download_url)
        return url, download_url, file_name


def download_flv(url, down_url, file_name):
    print
    "'%s' ---- Try Download ----" % url

    out_path = path.join(save_path, file_name)
    if not file_name:
        print
        "'%s' ** Not Found Link ** " % url
        return

    partial = False
    try:
        conn = urllib2.urlopen(down_url)
        length = conn.info()['Content-Length']
        length = int(length)
        if length < 1024 * 1024 * 150 or length > 1024 * 1024 * 700:
            print
            "*** '%s' is small! Skip!!!'%s' ***" % (url, length)
            return

        if path.exists(out_path):
            size = path.getsize(out_path)
            if size < length:
                r = "bytes=%s-" % size
                req = urllib2.Request(down_url, headers={"Range": r})
                conn = urllib2.urlopen(req)
                print
                "'%s' == Resume!! '%s' ==" % (url, file_name)
                print
                "'%s' == File     '%s' Size: %d/%d'" % (url, file_name, size, length)
                partial = True
            else:
                print
                "'%s' == Downloaded '%s' ==" % (url, file_name)
                return
    except:
        import traceback
        print
        traceback.format_exc()
        pool.spawn_n(download, url)
        return

    if partial:
        f = open(out_path, "rb+")
        f.seek(0, 2)
    else:
        f = open(out_path, "wb")

    print
    "'%s' == Start '%s' ==" % (url, file_name)
    while True:
        data = conn.read(1024 * 512)
        if not data:
            break
        f.write(data)
        # per = path.getsize(out_path) / float(length) * 100.0
        # print "'%s' == '%s' %d%% done. ==" % (url, file_name, per)
    print
    "'%s' == Finish '%s' ==" % (url, file_name)


def download(url):
    if url.find("premium.xhamster.com") >= 0:
        return
    url, download_url, file_name = get_download_url(url)
    download_flv(url, download_url, file_name)


def start(url, min_page=1, max_page=100):
    for i in xrange(min_page, max_page + 1):
        urls = get_pagelist(url, page=i)
        q.extend(urls)
    q.reverse()
    while q:
        url = q.pop()
        pool.spawn_n(download, url)


if __name__ == '__main__':

    for url in search_urls:
        start(url=url)
    pool.waitall()