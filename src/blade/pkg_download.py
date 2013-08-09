import urllib2
import hashlib
import time
import subprocess
import os

import console
import configparse
import load_build_files

from blade_util import get_cwd

def download(url, dest):
    res = urllib2.urlopen(url)
    content = ''
    if res:
        content = res.read()
        open(dest, 'w').write(content)
    return content

def parse_meta(data):
    meta_map = {}
    lines = data.split('\n')

    for line in lines:
        if not line:
            continue
        meta = line.split('=')
        meta_map.setdefault(meta[0], meta[1])
    return meta_map

def find_pkg_dir(source_dir):
    root_dir = load_build_files.find_blade_root_dir(get_cwd())
    cc_config = configparse.blade_config.get_config('cc_config')
    hostname = cc_config.get('hostname', '')
    if not hostname:
        console.error_exit("No hostname configured!")
    pkg_dir = hostname + '/' + source_dir
    download_dir = os.path.dirname(os.path.join(root_dir, source_dir))
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    return pkg_dir, download_dir

def download_pkg(source_dir):
    retry = 3
    base_url, download_dir = find_pkg_dir(source_dir)
    meta = download(base_url + '/META', '/tmp/META')
    meta_map = parse_meta(meta)
    name = meta_map.get('name', '')
    md5 = meta_map.get('md5', '').lower()
    if not name:
        return False

    for i in range(retry):
        try:
            res = download(base_url + '/' + name,  '/tmp/' + name)
        except HTTPError:
            console.error_exit("Can't find package `%s'"%(source_dir))
        except URLError:
            console.error_exit("Can't connect to remote host")

        calc_md5 = hashlib.md5(res).hexdigest()
        if calc_md5 == md5:
            break
        time.sleep(2**i)
    else:
        return False
    ret = subprocess.call('tar -xf /tmp/%s -C %s'%(name, download_dir), shell=True)
    return ret == 0
