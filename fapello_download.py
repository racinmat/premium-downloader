import os
from urllib.error import URLError
import os.path as osp
import requests
import yaml
from lxml import html
import progressbar
import urllib.request

hs = {
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://permit.pcta.org/application/'
}


def download_creator(creator_name, assume_naming=True, skip_failed=True):
    print(f'downloading {creator_name=}')
    s = requests.Session()
    s.headers.update(hs)
    print(f'loading failed urls')
    failed_txt = 'fapello_failed.txt'
    if osp.exists(failed_txt):
        with open(failed_txt, 'r', encoding='utf-8') as f:
            failed_urls = set(map(lambda x: x.strip(), f.readlines()))
    else:
        failed_urls = set()
    save_dir = 'fapello'
    base_url = 'https://fapello.com/{}/{}/'
    widgets = [progressbar.Percentage(), ' ', progressbar.Counter(), ' ', progressbar.Bar(), ' ',
               progressbar.FileTransferSpeed()]
    main_url = base_url[:-3].format(creator_name)
    response = s.get(main_url)
    if response.status_code == 302:
        print(f'creator page {main_url=} does not exist')
        return
    tree = html.fromstring(response.content)
    links = tree.xpath('//*[@id="content"]/div[1]/a')
    if len(links) == 0:
        print(f'creator page {main_url=} probably does not exist')
        return
    max_val = int(links[0].attrib['href'].split('/')[-2])
    pbar = progressbar.ProgressBar(widgets=widgets, max_value=max_val).start()
    for i in range(1, max_val + 1):
        pbar.update(i)
        i_url = base_url.format(creator_name, i)

        if assume_naming:
            save_path = osp.join(save_dir, creator_name, f'{creator_name}_{i:04}.jpg')
            if osp.exists(save_path):
                continue

        if skip_failed and i_url in failed_urls:
            continue
        response = s.get(i_url, allow_redirects=False)
        if response.status_code != 200:
            print(f'non-existing page, storing to the list')
            with open(failed_txt, 'a+', encoding='utf-8') as f:
                f.write(i_url + '\n')
            continue

        tree = html.fromstring(response.content)
        img_path = tree.xpath('//*[@id="wrapper"]/div[2]/div/div/div/div[2]/a/img')
        if len(img_path) == 0:
            # maybe video
            vid_path = tree.xpath('//*[@id="wrapper"]/div[2]/div/div/div/div[2]/video/source')
            if len(vid_path) == 0:
                print(f'skipping page {i_url=}, probably invalid')
                continue
            else:
                target_url = vid_path[0].attrib['src']
                save_path = osp.join(save_dir, creator_name, osp.basename(target_url))
        else:
            target_url = img_path[0].attrib['src']
            save_path = osp.join(save_dir, creator_name, osp.basename(target_url))
        os.makedirs(osp.dirname(save_path), exist_ok=True)
        if osp.exists(save_path):
            continue
        urllib.request.urlretrieve(target_url, save_path)
    pbar.finish()


def get_creator_list():
    with open('to_download_fapello.yml', 'r') as fp:
        try:
            return yaml.safe_load(fp)['stars']
        except yaml.YAMLError as exc:
            print(exc)


def main():
    creator_names = get_creator_list()
    for creator_name in creator_names:
        download_creator(creator_name)


if __name__ == '__main__':
    main()
