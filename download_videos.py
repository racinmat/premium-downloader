import sqlite3
from urllib import request
import requests
import progressbar
from crawl_videos_by_tag import get_porn_star_list
import os.path as osp


def main():
    hashtags_for_download = list(get_porn_star_list().keys())
    hashtags_list = ', '.join(hashtags_for_download)
    conn = sqlite3.connect('hashtags.db')
    conn.row_factory = sqlite3.Row
    videos_info = conn.execute(f'select * from videos where tag_id in ({hashtags_list}) and downloaded = 0').fetchall()
    widgets = [progressbar.Percentage(), ' ', progressbar.Counter(), ' ', progressbar.Bar(), ' ',
               progressbar.FileTransferSpeed()]
    pbar = progressbar.ProgressBar(widgets=widgets, max_value=len(videos_info)).start()

    for i, video_info in enumerate(videos_info):
        pbar.update(i)
        video_info = dict(video_info)
        share_id = video_info['share_id']
        file_name = f'videos/{share_id}.mp4'
        if osp.exists(file_name):
            with conn:
                conn.execute(f'UPDATE videos SET downloaded = 1 where share_id = {share_id}')
            continue
        download_link = video_info['download_url'].replace('watermark=1', 'watermark=0')
        # must have here headers, otherwise it behaves as api and does not serve the video
        response = requests.get(download_link, allow_redirects=True, headers={
            'User-Agent': 'Mozilla/5.0',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://permit.pcta.org/application/'
        })
        request.urlretrieve(response.url, file_name)
        with conn:
            conn.execute(f'UPDATE videos SET downloaded = 1 where share_id = {share_id}')

    pbar.finish()
    print('done')


if __name__ == '__main__':
    main()
