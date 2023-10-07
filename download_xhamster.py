# %%
import re
import sqlite3
from datetime import datetime

from splinter import Browser
from splinter.driver.webdriver.chrome import WebDriver

from a_downloader.functions import alive_check
from crawl_videos import create_ydl_client
from download_videos import download_ydl


# %%
def add_video_if_not_exists_xhamster(conn, video_id, video, source_name):
    if conn.execute(f'select exists(select 1 from videos_xhamster where video_id = \'{video_id}\')').fetchone()[0]:
        return
    with conn:
        conn.execute(
            'INSERT INTO videos_xhamster (video_id, video_url, star_name, added_timestamp) VALUES (?, ?, ?, ?)',
            (video_id, video, source_name, datetime.now().isoformat()))


def list_videos_page(browser: WebDriver, url):
    browser.visit(url)
    pages_div = browser.find_by_css(
        'body > div.main-wrap > main > div > article > div.pornstar-content > div.pornstar-content__main > div.index-videos.mixed-section > div.pager-section > div > ul > li')
    # one is prev and one is next
    pages_num = max(len(pages_div) - 2, 1)
    video_links = []
    for page in range(1, pages_num + 1):
        browser.visit(f"{url}/{page}")
        videos_div = browser.find_by_css(
            'body > div.main-wrap > main > div > article > div.pornstar-content > div.pornstar-content__main > div.index-videos.mixed-section > div:nth-last-child(2) > div').first
        videos_list = list(videos_div.find_by_css('div.thumb-list__item.video-thumb'))
        video_links += [i.find_by_css('a').first['href'] for i in videos_list]
    print(f'loaded {len(video_links)} videos from url {url} in total')
    return video_links


def list_videos_creator(conn, browser: WebDriver, creator):
    url = f'https://xhamster.com/creators/{creator}'
    videos_list = list_videos_page(browser, url)
    videos_list += list_videos_page(browser, f"{url}/exclusive")
    for video in videos_list:
        video_id = re.search('/videos/([\d\w-]+)', video).group(1)
        add_video_if_not_exists_xhamster(conn, video_id, video, creator)


def crawl_videos():
    conn = sqlite3.connect('links.db')
    conn.execute(
        "CREATE TABLE IF NOT EXISTS videos_xhamster (video_id varchar NOT NULL, star_name varchar NOT NULL, "
        "video_url varchar NOT NULL, downloaded integer NOT NULL DEFAULT 0, "
        "added_timestamp varchar default null, downloaded_timestamp varchar default null);")
    browser = Browser('chrome')
    browser.visit('https://xhamster.com')
    browser.find_by_css(
        'body > div.cookies-modal__wrapper > div.cookies-modal > div.cookies-modal-footer > div > button.xh-button.button.cmd-button-accept-all.green.large2.square > span').first.click()
    list_videos_creator(conn, browser, 'angel')
    print('done')
    browser.quit()


def check_url(url):
    alive_check(url)


def set_downloaded(conn, file_name, video_id):
    print(file_name, 'downloaded\n')
    with conn:
        conn.execute(
            f'UPDATE videos_xhamster SET downloaded = 1, downloaded_timestamp = "{datetime.now().isoformat()}" '
            f'where video_id = "{video_id}"')


def download_videos():
    ydl = create_ydl_client('videos_xhamster', False)
    pbar = download_ydl(ydl, 'select * from videos_xhamster where downloaded = 0', set_downloaded, check_url)
    pbar.finish()
    print('done')


def main():
    # crawl_videos()
    download_videos()


# %%
if __name__ == '__main__':
    main()
