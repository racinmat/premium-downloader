import os
import re
import subprocess
import traceback

import yaml


# upload to server and then run `source activate py310`
def examine_dir(a_dir, print_files, show_errors, max_depth, depth=0):
    output_bytes = subprocess.check_output(f'mega-ls -lh "{a_dir}"', shell=True)
    try:
        output = output_bytes.decode('utf-8').rstrip()
        parse_ls(a_dir, print_files, show_errors, max_depth, output, depth)
    except Exception as e:
        if show_errors:
            traceback.print_exc()
            hash_a_dir = str(hash(a_dir))
            print(f'error in decoding {a_dir}, storing it as {hash_a_dir}')
            with open(f'/volume1/shared_data/video/other/of_leaks/error_output_{hash_a_dir}.txt', 'wb') as f:
                f.write(output_bytes)


def parse_ls(a_dir, print_files, show_errors, max_depth, output, depth=0):
    # print(output)
    lines = output.split('\n')
    header_line = lines[0]
    rows_line = lines[1:]
    headers = re.split('\s+', header_line)
    rows = [re.split('\s+', r, maxsplit=len(headers)) for r in rows_line]
    # print('rows:')
    # print(rows)
    for flags, vers, size, date1, date2, name in rows:
        is_dir = flags == 'd---'
        if is_dir:
            inner_dir = a_dir + '/' + name
            size_lines = subprocess.check_output(f'mega-du -h "{inner_dir}"', shell=True).decode('utf-8')
            size_line = size_lines.split('\n')[1]
            size = ' '.join(re.split('\s+', size_line)[-2:])
            print(f'{" " * 4 * (depth+1)}{size}, {name}')
            # print(f'{" " * 2 * (depth+1)}examining it')
            if depth + 1 <= max_depth:
                examine_dir(inner_dir, print_files, show_errors, max_depth, depth+1)
        else:
            size = f'{size} {date1}'
            date1 = date2
            # print(f'{size=}, {date1=}, {date2}, {name=}')
            date2, name = name.split(' ', maxsplit=1)
            if print_files:
                print(f'{" " * 4 * (depth+1)}{size}, {name}')


def main():
    with open('mega_link.yaml', mode='r', encoding='utf-8') as fp:
        main_link = yaml.safe_load(fp)
    # main_dir = main_link
    # os.system(f'mega-login {main_dir}')
    print_files = False
    show_errors = False
    max_depth = 4
    examine_dir('', print_files, show_errors, max_depth)


if __name__ == '__main__':
    main()
# run as
# source activate py310
# cd ~/tmp/pycharm_project_395
# python mega_list_sizes.py
# python mega_list_sizes.py > /volume1/shared_data/video/other/of_leaks/total_output.txt 2>&1
# python mega_list_sizes.py > /volume1/shared_data/video/other/of_leaks/total_output_dirs_only.txt 2>&1
# python mega_list_sizes.py > /volume1/shared_data/video/other/of_leaks/total_output_small.txt 2>&1
# python mega_list_sizes.py > /volume1/shared_data/video/other/of_leaks/total_output_small_5.txt 2>&1
# python mega_list_sizes.py > /volume1/shared_data/video/other/of_leaks/total_output_small_4.txt 2>&1
