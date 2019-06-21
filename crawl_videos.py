import json
import sqlite3
from io import StringIO
from splinter.driver.webdriver.chrome import WebDriver
from client import Client
import re


def create_client():
    with open('credentials.json', mode='r', encoding='utf-8') as fp:
        credentials = json.load(fp)
    username = credentials['username']
    password = credentials['password']
    client = Client(username, password)
    browser = client.login()
    return browser


def get_links_for_star_videos(browser, name, video_links):
    pages_div = browser.find_by_css('body > div.wrapper > div > div.nf-wrapper > div.pagination3 > ul')
    other_pages = [] if len(pages_div) == 0 else pages_div.first.find_by_css(
        'li.page_number')  # sometimes pagination is missing at all
    if len(other_pages) == 0:
        pages_num = 1
    else:
        pages_num = int(other_pages.last.text)
    video_counter_sel = 'body > div.wrapper > div > div:nth-child(13) > div.showingCounter.pornstarVideosCounter'
    if len(browser.find_by_css(video_counter_sel)) == 0 and len(browser.find_by_css('#pornstarsVideoSection')) == 0:
        #   no videos
        print(f'no private videos for pornstar {name}')
        return video_links
    videos_str = browser.find_by_css(video_counter_sel).text
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
    else:
        raise RuntimeError('error with profile, someting unknown')
    return video_links


def channel_all_premium_videos(browser: WebDriver, name):
    browser.visit(f'https://www.pornhubpremium.com/channels/{name}/videos?premium=1')
    pages_div = browser.find_by_css('#channelsProfile > div.pagination3')
    if len(pages_div) == 0:  # no pagination, so only one page
        pages_num = 1
    else:
        pages_num = int(pages_div.first.find_by_css('li.page_number').last.text)

    video_links = []
    for page in range(1, pages_num + 1):
        browser.visit(f'https://www.pornhubpremium.com/channels/{name}/videos?premium=1&page={page}')
        videos_div = browser.find_by_css('#moreData').first
        videos_list = list(videos_div.find_by_css('li.videoblock'))
        video_links += [i.find_by_css('div > div.thumbnail-info-wrapper.clearfix > span > a').first['href'] for i in
                        videos_list]
    print(f'loaded {len(video_links)} videos for pornstar {name} in total')
    return video_links


def get_porn_star_list():
    return [
        'sasha-grey', 'sasha-foxxx', 'asa-akira', 'madison-scott', 'riley-reid',
        'skin-diamond', 'maitresse-madeline', 'ashley-jane', 'lorelei-lee', 'amber-rayne',
        'gia-dimarco', 'dani-daniels', 'krissy-lynn', 'madison-young', 'nora-skyy',
        'dillion-harper', 'kathia-nobili', 'charli-piper', 'piper-perri', 'melody-marks',
        'ella-nova', 'lola-fae', 'jenna-presley', 'jasmine-jae', 'pussykat', 'jayden-lee',
        'ashley-fires', 'kate-truu', 'rae-lil-black', 'ashlynn-taylor', 'kristina-rose',
        'felony', 'anabelle-pync', 'ariana-marie', 'abella-danger', 'kimmy-granger',
        'julianna-vega', 'veronica-avluv', 'aiden-starr', 'kasey-warner', 'christie-stevens',
        'katie-kox', 'sabrina-banks', 'lexi-lore', 'alli-rae', 'janice-griffith',
        'sophie-dee', 'linet-a-lynette', 'lexi-belle', 'francesca-le', 'kelly-divine',
        'chanel-preston', 'vicki-chase', 'casey-calvert', 'jasmine-callipygian', 'athena-rayne',
        'paisley-rae', 'ava-taylor', 'jia-lissa', 'amanda-monroe', 'maria-pie',
        'natalia-starr', 'kendra-james', 'harley-dean', 'jamie-valentine', 'brianna-beach',
        'penny-flame', 'charlotte-sartre', 'lena-kelly', 'lucy-heart', 'nesty',
        'cadence-lux', 'sheena-rose', 'mona-wales', 'aidra-fox', 'natasha-nice',
        'alaina-dawson', 'rossy-bush',
    ]


def get_channel_list():
    return [
        'mofos', 'harmonyvision', 'helpless-teens', 'theupperfloor', 'sexandsubmission',
        'divinebitches', 'kink-university', 'thetrainingofo',
    ]


def main():
    browser = create_client()
    porn_stars = get_porn_star_list()
    channels = get_channel_list()

    conn = sqlite3.connect('links.db')
    conn.execute(
        "CREATE TABLE IF NOT EXISTS videos (video_id varchar NOT NULL, star_name varchar NOT NULL, "
        "video_url varchar NOT NULL, downloaded integer NOT NULL DEFAULT 0, download_forbidden int default NULL);")

    for star_name in porn_stars:
        videos_list = porn_star_all_premium_videos(browser, star_name)
        for video in videos_list:
            video_id = re.search('viewkey=([\d\w]+)', video).group(1)
            if conn.execute(f'select exists(select 1 from videos where video_id = \'{video_id}\')').fetchone()[0]:
                continue
            with conn:
                conn.execute('INSERT INTO videos (video_id, video_url, star_name) VALUES (?, ?, ?)',
                             (video_id, video, star_name))
    print('done stars\n')

    for channel in channels:
        videos_list = porn_star_all_premium_videos(browser, channel)
        for video in videos_list:
            video_id = re.search('viewkey=([\d\w]+)', video).group(1)
            if conn.execute(f'select exists(select 1 from videos where video_id = \'{video_id}\')').fetchone()[0]:
                continue
            with conn:
                conn.execute('INSERT INTO videos (video_id, video_url, star_name) VALUES (?, ?, ?)',
                             (video_id, video, channel))
    print('done channels\n')
    print('done everything\n')


if __name__ == '__main__':
    main()
