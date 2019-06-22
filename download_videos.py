import sqlite3
from time import sleep
from urllib import request
from urllib.error import URLError

import requests
import progressbar
import os.path as osp

from crawl_videos import create_client


def is_download_forbidden(browser, conn, video_id):
    download_blocked_div = '.video-actions-tabs > .video-action-tab.download-tab > .verifyEmailWrapper'
    download_blocked_message = 'The download feature of this video has been disabled by'
    if len(browser.find_by_css(download_blocked_div)) > 0 and download_blocked_message in browser.find_by_css(
            download_blocked_div).text:
        print('video download is forbidden\n')
        with conn:
            conn.execute(f'UPDATE videos SET downloaded = 0, download_forbidden = 1 where video_id = "{video_id}"')
        return True
    return False


def click_download_tab(browser):
    download_tab_button_sel = '.tab-menu-item[data-tab="download-tab"]'
    download_tab_button_active_sel = '.tab-menu-item.active[data-tab="download-tab"]'
    counter = 0
    while not browser.is_element_present_by_css(download_tab_button_active_sel):
        if counter > 10:
            raise RuntimeError('can not click on download tab')
        sleep(0.1)  # Time in seconds
        browser.find_by_css(download_tab_button_sel).click()
        print('clicking on it\n')
        counter += 1


def main():
    browser = create_client()

    conn = sqlite3.connect('links.db')
    conn.row_factory = sqlite3.Row
    videos_info = conn.execute(f'select * from videos where downloaded = 0 and download_forbidden isnull').fetchall()
    widgets = [progressbar.Percentage(), ' ', progressbar.Counter(), ' ', progressbar.Bar(), ' ',
               progressbar.FileTransferSpeed()]
    pbar = progressbar.ProgressBar(widgets=widgets, max_value=len(videos_info)).start()

    for i, video_info in enumerate(videos_info):
        pbar.update(i)
        video_info = dict(video_info)
        video_id = video_info['video_id']
        browser.visit(video_info['video_url'])

        while browser.is_element_present_by_css('.recaptchaContent'):  # sometimes wild captcha appears
            print("CAPTCHA NEEDED")
            sleep(60)

        if browser.is_element_present_by_css('.removed'):
            # video has been removed
            print('video has been removed\n')
            with conn:
                conn.execute(f'UPDATE videos SET download_forbidden = 1 where video_id = "{video_id}"')
            continue

        video_title = browser.find_by_css('#videoTitle').text  # type: str
        # because of fucking windows
        video_title = video_title.replace(':', '').replace('?', '').replace('*', '').replace('"', '').replace('/', '')\
            .replace('\\', '')
        browser.find_by_id('player').click()  # pausing video
        browser.find_by_tag('body')._element.send_keys('M')  # muting video

        file_name = f'videos/{video_id}-{video_title}.mp4'
        if osp.exists(file_name):
            with conn:
                conn.execute(f'UPDATE videos SET downloaded = 1 where video_id = "{video_id}"')
            continue

        if browser.is_element_present_by_css('.tab-menu-item.js-paidDownload[data-tab="download-tab"]'):
            # video has been removed
            print('video download is paid\n')
            with conn:
                conn.execute(f'UPDATE videos SET download_forbidden = 1 where video_id = "{video_id}"')
            continue

        click_download_tab(browser)

        if is_download_forbidden(browser, conn, video_id):
            continue

        download_link = get_download_link(browser)
        # must have here headers, otherwise it behaves as api and does not serve the video
        for _ in range(5):
            try:
                request.urlretrieve(download_link, file_name)
                break
            except URLError:
                print('connection failed, trying again\n')

        print(file_name, 'downloaded\n')
        with conn:
            conn.execute(f'UPDATE videos SET downloaded = 1 where video_id = "{video_id}"')

    pbar.finish()
    print('done')


def get_download_link(browser):
    sizes = [720, 480]
    download_link = None
    for size in sizes:
        if len(browser.find_link_by_text(f' {size}p')) == 0:
            # size not existing, trying another
            continue
        download_link = browser.find_link_by_text(f' {size}p').first['href']
        break
    if download_link is None:
        raise RuntimeError('link for corresponding size not found')
    return download_link


if __name__ == '__main__':
    main()
