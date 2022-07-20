import os
from urllib.error import URLError
import os.path as osp
import requests
from lxml import html
import progressbar

hs = {
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://permit.pcta.org/application/'
}


def download_creator(creator_name):
    s = requests.Session()
    s.headers.update(hs)

    save_dir = 'fapello'
    base_url = 'https://fapello.com/{}/{}'
    widgets = [progressbar.Percentage(), ' ', progressbar.Counter(), ' ', progressbar.Bar(), ' ',
               progressbar.FileTransferSpeed()]
    main_url = base_url[:-3].format(creator_name)
    response = s.get(main_url)
    tree = html.fromstring(response.content)
    max_val = int(tree.xpath('//*[@id="content"]/div[1]/a')[0].attrib['href'].split('/')[-2])
    pbar = progressbar.ProgressBar(widgets=widgets, max_value=max_val).start()
    for i in range(1, max_val+1):
        pbar.update(i)
        i_url = base_url.format(creator_name, i)
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


def main():
    creator_names = ['hemulka', 'bonbibonkers']
    for creator_name in creator_names:
        download_creator(creator_name)


if __name__ == '__main__':
    main()
