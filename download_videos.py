import sqlite3
from urllib import request
import requests
import progressbar
import os.path as osp

from crawl_videos import create_client


def main():
    browser = create_client()

    conn = sqlite3.connect('links.db')
    conn.row_factory = sqlite3.Row
    videos_info = conn.execute(f'select * from videos where downloaded = 0').fetchall()
    widgets = [progressbar.Percentage(), ' ', progressbar.Counter(), ' ', progressbar.Bar(), ' ',
               progressbar.FileTransferSpeed()]
    pbar = progressbar.ProgressBar(widgets=widgets, max_value=len(videos_info)).start()

    for i, video_info in enumerate(videos_info):
        pbar.update(i)
        video_info = dict(video_info)
        video_id = video_info['video_id']
        browser.visit(video_info['video_url'])
        video_title = browser.find_by_css('#videoTitle').text
        file_name = f'videos/{video_id}-{video_title}.mp4'
        if osp.exists(file_name):
            with conn:
                conn.execute(f'UPDATE videos SET downloaded = 1 where video_id = {video_id}')
            continue
        sizes = [720, 480]
        download_link = None
        for size in sizes:
            if list(browser.find_link_by_text(f' {size}p')) == 0:
                # size not existing, trying another
                continue
            download_link = browser.find_link_by_text(f' {size}p').first['href']
            break
        if download_link is None:
            raise RuntimeError('link for corresponding size not found')
        # must have here headers, otherwise it behaves as api and does not serve the video
        request.urlretrieve(download_link, file_name)
        # response = requests.get(download_link, allow_redirects=True, headers={
        #     'User-Agent': 'Mozilla/5.0',
        #     'X-Requested-With': 'XMLHttpRequest',
        #     'Referer': 'https://permit.pcta.org/application/'
        # })
        # request.urlretrieve(response.url, file_name)
        with conn:
            conn.execute(f'UPDATE videos SET downloaded = 1 where video_id = {video_id}')

    pbar.finish()
    print('done')


if __name__ == '__main__':
    main()