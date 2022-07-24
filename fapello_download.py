import os
from urllib.error import URLError
import os.path as osp
import requests
import yaml
from lxml import html
import progressbar

hs = {
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://permit.pcta.org/application/'
}


def download_creator(creator_name, assume_naming=True):
    print(f'downloading {creator_name=}')
    s = requests.Session()
    s.headers.update(hs)

    save_dir = 'fapello'
    base_url = 'https://fapello.com/{}/{}'
    widgets = [progressbar.Percentage(), ' ', progressbar.Counter(), ' ', progressbar.Bar(), ' ',
               progressbar.FileTransferSpeed()]
    main_url = base_url[:-2].format(creator_name)
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
        response = s.get(i_url)
        tree = html.fromstring(response.content)
        img_path = tree.xpath('//*[@id="wrapper"]/div[2]/div/div/div/div[2]/a/img')
        if len(img_path) == 0:
            print(f'skipping page {i_url=}, probably invalid')
            continue
        image_url = img_path[0].attrib['src']
        save_path = osp.join(save_dir, creator_name, osp.basename(image_url))
        os.makedirs(osp.dirname(save_path), exist_ok=True)
        if osp.exists(save_path):
            continue
        response = s.get(image_url)
        if response.status_code != 200:
            raise URLError
        with open(save_path, 'wb') as f:
            f.write(response.content)
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
