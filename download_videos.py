import sqlite3
from datetime import datetime
from time import sleep
from urllib import request
from urllib.error import URLError

import requests
import progressbar
import os.path as osp

import youtube_dl
from splinter.driver.webdriver.chrome import WebDriver

from a_downloader.functions import custom_dl_download, ph_url_check, ph_alive_check, get_dl_location
from crawl_videos import create_client, create_ydl_client


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


def click_download_tab(browser, download_tab_button_sel):
    download_tab_button_active_sel = '.tab-menu-item.active[data-tab="download-tab"]'
    counter = 0
    while not browser.is_element_present_by_css(download_tab_button_active_sel):
        if counter > 10:
            print('can not click on download tab')
            return False
        sleep(0.1)  # Time in seconds
        button = browser.find_by_css(download_tab_button_sel)
        browser.find_by_text('The download feature of this video has been disabled ')
        if len(button) == 0:
            print('disabled video download, trying alternative')
            return False
        button.click()
        print('clicking on it\n')
        counter += 1
    return True


def download_using_youtube_dl(ydl, url) -> bool:
    ph_url_check(url)
    ph_alive_check(url)
    ydl._download_retcode = 0   # because this is not set to 0 before each download, it is turned just from 0 to 1
    # so the line above resets it to default state
    download_ret_code = ydl.download([url])
    return download_ret_code == 0


def set_downloaded(conn, file_name, video_id):
    print(file_name, 'downloaded\n')
    with conn:
        conn.execute(
            f'UPDATE videos SET downloaded = 1, downloaded_timestamp = "{datetime.now().isoformat()}" '
            f'where video_id = "{video_id}"')


def download_official():
    browser: WebDriver = create_client()
    conn, videos_info = list_videos()
    pbar = prepare_pbar(videos_info)
    for i, video_info in enumerate(videos_info):
        pbar.update(i)
        video_info = dict(video_info)
        video_id = video_info['video_id']
        video_url = video_info['video_url']
        browser.visit(video_url)

        while browser.is_element_present_by_css('.recaptchaContent'):  # sometimes wild captcha appears
            print("CAPTCHA NEEDED")
            sleep(60)

        if browser.is_element_present_by_css('.removed'):
            # video has been removed
            print('video has been removed\n')
            with conn:
                conn.execute(f'UPDATE videos SET download_forbidden = 1 where video_id = "{video_id}"')
            continue
        if not browser.is_element_visible_by_css(
                '.premiumIconTitleOnVideo') and not browser.is_element_present_by_css('#videoTitle'):
            # video has been removed
            print('video is somehow broken and not premiuzm\n')
            with conn:
                conn.execute(f'UPDATE videos SET download_forbidden = 1 where video_id = "{video_id}"')
            continue

        video_title = browser.find_by_css('#videoTitle').text  # type: str
        # because of fucking windows
        video_title = video_title.replace(':', '').replace('?', '').replace('*', '').replace('"', '').replace('/', '') \
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

        download_tab_button_sel = '.tab-menu-item[data-tab="download-tab"]'
        vr_tab_button_sel = '.tab-menu-item[data-tab="vr-tab"]'
        if not browser.is_element_present_by_css(download_tab_button_sel) \
                and browser.is_element_present_by_css(vr_tab_button_sel):
            # video has been removed
            print('video is vr, no download\n')
            with conn:
                conn.execute(f'UPDATE videos SET download_forbidden = 1 where video_id = "{video_id}"')
            continue

        click_download_tab(browser, download_tab_button_sel)
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

        set_downloaded(conn, file_name, video_id)
    return pbar


def download_ydl():
    ydl = create_ydl_client()
    conn, videos_info = list_videos()
    pbar = prepare_pbar(videos_info)
    for i, video_info in enumerate(videos_info):
        pbar.update(i)
        video_info = dict(video_info)
        video_id = video_info['video_id']
        video_url = video_info['video_url']
        download_success = download_using_youtube_dl(ydl, video_url)
        if download_success:
            set_downloaded(conn, video_url, video_id)
        else:
            print(f'failed to download the video {video_id}, {video_url}')
    return pbar


def prepare_pbar(videos_info):
    widgets = [progressbar.Percentage(), ' ', progressbar.Counter(), ' ', progressbar.Bar(), ' ',
               progressbar.FileTransferSpeed()]
    pbar = progressbar.ProgressBar(widgets=widgets, max_value=len(videos_info)).start()
    return pbar


def list_videos():
    conn = sqlite3.connect('links.db')
    conn.row_factory = sqlite3.Row
    videos_info = conn.execute(f'select * from videos where downloaded = 0 and download_forbidden isnull').fetchall()
    return conn, videos_info


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


def main():
    use_ydl = True
    if use_ydl:
        pbar = download_ydl()
    else:
        pbar = download_official()

    pbar.finish()
    print('done')


if __name__ == '__main__':
    main()
