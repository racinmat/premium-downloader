import json
from datetime import datetime

import yaml
import sqlite3
from io import StringIO

from splinter.driver.webdriver.chrome import WebDriver
from client import Client
import re


def create_client():
    with open('credentials.yml', mode='r', encoding='utf-8') as fp:
        credentials = yaml.safe_load(fp)
    username = credentials['username']
    password = credentials['password']
    client = Client(username, password)
    browser = client.login()
    return client, browser


def create_ydl_client(base_dir='videos', use_youtube_dl=True):
    with open('credentials.yml', mode='r', encoding='utf-8') as fp:
        credentials = yaml.safe_load(fp)
    username = credentials['username']
    password = credentials['password']
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{base_dir}/%(id)s-%(title)s.mp4',
        'nooverwrites': True,
        'no_warnings': False,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'verbose': True,
        'username': username,
        'password': password,
    }
    if use_youtube_dl:
        import youtube_dl
        ydl = youtube_dl.YoutubeDL(ydl_opts)
    else:
        import yt_dlp
        ydl = yt_dlp.YoutubeDL(ydl_opts)
    return ydl


def get_links_for_star_videos(browser, name, video_links):
    pages_div = browser.find_by_css('body > div.wrapper > div > div.nf-wrapper > div.pagination3 > ul')
    other_pages = [] if len(pages_div) == 0 else pages_div.first.find_by_css(
        'li.page_number')  # sometimes pagination is missing at all
    if len(other_pages) == 0:
        pages_num = 1
    else:
        pages_num = int(other_pages.last.text)
    video_counter_sel = 'body > div.wrapper > div > div:nth-child({}) > div.showingCounter.pornstarVideosCounter'
    video_counter_sel1 = video_counter_sel.format(13)
    video_counter_sel2 = video_counter_sel.format(12)
    video_counter_sel3 = 'body > div.wrapper > div.container > div:nth-child(15) > div.showingCounter.pornstarVideosCounter'
    if len(browser.find_by_css(video_counter_sel1)) == 0 and len(browser.find_by_css('#pornstarsVideoSection')) == 0:
        #   no videos
        print(f'no private videos for pornstar {name}')
        return video_links
    elif len(browser.find_by_css(video_counter_sel1)) > 0:
        videos_str = browser.find_by_css(video_counter_sel1).text
    elif len(browser.find_by_css(video_counter_sel2)) > 0:
        videos_str = browser.find_by_css(video_counter_sel2).text
    else:
        videos_str = browser.find_by_css(video_counter_sel3).text
    total_videos_num = int(videos_str.split(' ')[-1])
    for page in range(1, pages_num + 1):
        browser.visit(f'https://www.pornhubpremium.com/pornstar/{name}?premium=1&page={page}')
        videos_div = browser.find_by_css('#pornstarsVideoSection').first
        videos_list = list(videos_div.find_by_css('li.videoblock'))
        video_links += [i.find_by_css('div > div.thumbnail-info-wrapper.clearfix > span > a').first['href'] for i in
                        videos_list]
    print(f'loaded {len(video_links)} videos for pornstar {name} in total')
    assert len(video_links) == total_videos_num
    return video_links


def get_links_for_star_profile(browser, name, video_links):
    browser.visit(f'https://www.pornhubpremium.com/pornstar/{name}/videos/premium')
    pages_div = browser.find_by_css(
        '#profileContent > div.profileContentLeft > section > div > div.nf-wrapper > div.pagination3')
    if len(pages_div) == 0:  # no pagination, so only one page
        pages_num = 1
    else:
        pages_num = int(pages_div.first.find_by_css('li.page_number').last.text)
    for page in range(1, pages_num + 1):
        browser.visit(f'https://www.pornhubpremium.com/pornstar/{name}/videos/premium?page={page}')
        videos_div = browser.find_by_css('#moreData').first
        videos_list = list(videos_div.find_by_css('li.videoblock'))
        video_links += [i.find_by_css('div > div.thumbnail-info-wrapper.clearfix > span > a').first['href'] for i in
                        videos_list]
    print(f'loaded {len(video_links)} videos for pornstar {name} in total')
    return video_links


def porn_star_all_premium_videos(browser: WebDriver, name):
    # example of type 1, no pagination: https://www.pornhubpremium.com/pornstar/sasha-foxxx/videos/premium
    # example of type 1, pagination: https://www.pornhubpremium.com/pornstar/asa-akira/videos/premium
    # example of type 2, no pagination: https://www.pornhubpremium.com/pornstar/madison-scott?premium=1
    # example of type 2, pagination: https://www.pornhubpremium.com/pornstar/sasha-grey?premium=1&page=2
    # there are 2 types of porn star pages, fuck it
    browser.visit(f'https://www.pornhubpremium.com/pornstar/{name}?premium=1')
    video_links = []
    if browser.is_element_present_by_id('profileHome'):
        video_links = get_links_for_star_profile(browser, name, video_links)
    elif browser.is_element_present_by_id('pornstarVideos'):
        video_links = get_links_for_star_videos(browser, name, video_links)
    # there has been redirect
    elif browser.url == 'https://www.pornhubpremium.com/pornstars':
        print(f'star {name} does not exist')
        return []
    else:
        raise RuntimeError('error with profile, someting unknown')
    return video_links


def channel_all_premium_videos(browser: WebDriver, name):
    browser.visit(f'https://www.pornhubpremium.com/channels/{name}/videos?premium=1')
    pages_list = browser.find_by_css('#channelsProfile > div.pagination3 > ul > li')
    if browser.title == 'Page Not Found':
        print(f'Channel {name} does not exist.')
        return []
    elif len(pages_list) in [0, 1]:  # no pagination, so only one page
        pages_num = 1
    else:
        pages_num = int(browser.find_by_css('#channelsProfile > div.pagination3 > ul > li.page_number').last.text)

    video_links = []
    for page in range(1, pages_num + 1):
        browser.visit(f'https://www.pornhubpremium.com/channels/{name}/videos?premium=1&page={page}')
        videos_div = browser.find_by_css('ul#showAllChanelVideos').first
        videos_list = list(videos_div.find_by_css('li.videoblock'))
        video_links += [i.find_by_css('div > div.thumbnail-info-wrapper.clearfix > span > a').first['href'] for i in
                        videos_list]
    print(f'loaded {len(video_links)} videos for pornstar {name} in total')
    return video_links


def models_all_public_videos(browser: WebDriver, name):
    browser.visit(f'https://www.pornhub.com/model/{name}/videos')
    sel1 = '#channelsProfile > div.pagination3 > ul > li'
    sel2 = '#videosTab > div > div > div.nf-wrapper > div.pagination3.paginationGated > ul > li'
    pages_list1 = browser.find_by_css(sel1)
    pages_list2 = browser.find_by_css(sel2)
    sel, pages_list = max((sel1, pages_list1), (sel2, pages_list2), key=lambda x: len(x[1]))
    if browser.title == 'Page Not Found':
        print(f'Channel {name} does not exist.')
        return []
    elif len(pages_list) in [0, 1]:  # no pagination, so only one page
        pages_num = 1
    else:
        pages_num = int(browser.find_by_css(f'{sel}.page_number').last.text)

    video_links = []
    for page in range(1, pages_num + 1):
        browser.visit(f'https://www.pornhub.com/model/{name}/videos?page={page}')
        videos_div = browser.find_by_css('ul#mostRecentVideosSection').first
        videos_list = list(videos_div.find_by_css('li.videoblock'))
        video_links += [i.find_by_css('div > div.thumbnail-info-wrapper.clearfix > span > a').first['href'] for i in
                        videos_list]
    print(f'loaded {len(video_links)} videos for pornstar {name} in total')
    return video_links


def get_porn_star_list():
    with open('to_download.yml', 'r') as fp:
        try:
            return yaml.safe_load(fp)['stars']
        except yaml.YAMLError as exc:
            print(exc)


def get_channel_list():
    with open('to_download.yml', 'r') as fp:
        try:
            return yaml.safe_load(fp)['channels']
        except yaml.YAMLError as exc:
            print(exc)


def get_model_list():
    with open('to_download.yml', 'r') as fp:
        try:
            return yaml.safe_load(fp)['models']
        except yaml.YAMLError as exc:
            print(exc)


def add_video_if_not_exists(conn, video_id, video, source_name):
    if conn.execute(f'select exists(select 1 from videos where video_id = \'{video_id}\')').fetchone()[0]:
        return
    with conn:
        conn.execute('INSERT INTO videos (video_id, video_url, star_name, added_timestamp) VALUES (?, ?, ?, ?)',
                     (video_id, video, source_name, datetime.now().isoformat()))


def main():
    client, browser = create_client()
    porn_stars = get_porn_star_list()
    channels = get_channel_list()
    models = get_model_list()

    conn = sqlite3.connect('links.db')
    conn.execute(
        "CREATE TABLE IF NOT EXISTS videos (video_id varchar NOT NULL, star_name varchar NOT NULL, "
        "video_url varchar NOT NULL, downloaded integer NOT NULL DEFAULT 0, download_forbidden int default NULL, "
        "added_timestamp varchar default null, downloaded_timestamp varchar default null);")

    # for star_name in porn_stars:
    #     videos_list = porn_star_all_premium_videos(browser, star_name)
    #     for video in videos_list:
    #         video_id = re.search('viewkey=([\d\w]+)', video).group(1)
    #         add_video_if_not_exists(conn, video_id, video, star_name)
    # print('done stars\n')
    #
    # for channel in channels:
    #     videos_list = channel_all_premium_videos(browser, channel)
    #     for video in videos_list:
    #         video_id = re.search('viewkey=([\d\w]+)', video).group(1)
    #         add_video_if_not_exists(conn, video_id, video, channel)
    # print('done channels\n')

    browser = client.login('https://www.pornhub.com/login', 'https://www.pornhub.com/')
    for model in models:
        videos_list = models_all_public_videos(browser, model)
        for video in videos_list:
            video_id = re.search('viewkey=([\d\w]+)', video).group(1)
            add_video_if_not_exists(conn, video_id, video, model)
    print('done models\n')
    print('done everything\n')


if __name__ == '__main__':
    main()
# todo: add script to move videos to dir by star name
