import json
import sqlite3
from io import StringIO

from client import Client


def create_client():
    with open('credentials.json', mode='r', encoding='utf-8') as fp:
        credentials = json.load(fp)
    username = credentials['username']
    password = credentials['password']
    client = Client(username, password)
    client.login()
    return client


def search_tags_by_name(client, query):
    results = client.search_hashtag(query)
    return [{'cid': i['challenge_info']['cid'], 'cha_name': i['challenge_info']['cha_name']} for i in
            results['challenge_list']]


def videos_by_hashtag(client, tag_id, count=100):
    results = client.list_hashtag(tag_id, count)
    return results_to_videos_info(results)


def videos_by_hashtag_paginated(client, tag_id, count=2000, per_page=100):
    videos = []
    prev_cursor = 0
    for page in range(round(count / per_page)):
        results = client.list_hashtag(tag_id, count=per_page, offset=prev_cursor)
        videos_page = results_to_videos_info(results)
        print(f'loaded {len(videos_page)} videos for hashtag {tag_id} in cursor {prev_cursor}')
        videos += videos_page
        if results['cursor'] == prev_cursor:
            print('end of cursor, aborting')
            break
        prev_cursor = results['cursor']
    print(f'loaded {len(videos)} videos for hashtag {tag_id} in total')
    return videos


def results_to_videos_info(results):
    return [{
        'download_url': i['video']['download_addr']['url_list'][0],
        'share_id': i['aweme_id'],
        'download_id': i['video']['download_addr']['uri'],
        'share_url': i['share_url'],
        'create_time': i['create_time'],
    } for i in results['aweme_list']]


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
        'chanel-preston', 'vicki-chase', 'casey-calvert', 'jasmine-callipygian'
    ]

def main():
    client = create_client()
    porn_stars = get_porn_star_list()

    conn = sqlite3.connect('links.db')
    conn.execute(
        "CREATE TABLE IF NOT EXISTS videos (tag_id varchar NOT NULL, share_url varchar NOT NULL, "
        "downloaded integer NOT NULL DEFAULT 0, share_id varchar NOT NULL, download_url varchar NOT NULL, "
        "download_id varchar NOT NULL, create_time integer NOT NULL);")

    for tag_id in porn_stars:
        videos_list = videos_by_hashtag_paginated(client, tag_id, count=10000, per_page=100)
        for video in videos_list:
            share_id = video['share_id']
            if conn.execute(f'select exists(select 1 from videos where share_id = \'{share_id}\')').fetchone()[0]:
                continue
            with conn:
                conn.execute('INSERT INTO videos (tag_id, share_url, share_id, download_url, download_id, create_time) '
                             'VALUES (?, ?, ?, ?, ?, ?)',
                             (tag_id, video['share_url'], video['share_id'], video['download_url'],
                              video['download_id'], video['create_time']))

    print('done')


if __name__ == '__main__':
    main()
