import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

BASE_URL = 'https://icphysweb.z13.web.core.windows.net/simulation.html'
BASE_DIR = 'downloaded_simulation'

# 需要递归下载的资源类型
RESOURCE_EXTS = ['.js', '.css', '.png', '.jpg', '.jpeg', '.svg', '.gif', '.ico', '.json', '.html', '.htm', '.webp']

visited = set()

def safe_filename(url):
    # 将url转为本地安全路径
    parsed = urlparse(url)
    path = parsed.path.lstrip('/')
    return os.path.join(BASE_DIR, path)

def download_file(url):
    local_path = safe_filename(url)
    if os.path.exists(local_path):
        return local_path
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        with open(local_path, 'wb') as f:
            f.write(resp.content)
        print(f'下载: {url} -> {local_path}')
        return local_path
    except Exception as e:
        print(f'下载失败: {url}，原因: {e}')
        return None

def is_resource(url):
    return any(url.lower().endswith(ext) for ext in RESOURCE_EXTS)

def crawl(url):
    if url in visited:
        return
    visited.add(url)
    print(f'爬取: {url}')
    local_path = download_file(url)
    if not local_path or not (url.endswith('.html') or url.endswith('.htm')):
        return
    # 解析HTML，递归下载资源
    with open(local_path, 'r', encoding="utf-8", errors='ignore') as f:
        soup = BeautifulSoup(f, 'html.parser')
    # 处理<link>、<script>、<img>等标签
    tags_attrs = [
        ('link', 'href'),
        ('script', 'src'),
        ('img', 'src'),
        ('iframe', 'src'),
        ('source', 'src'),
        ('audio', 'src'),
        ('video', 'src'),
        ('a', 'href'),
    ]
    for tag, attr in tags_attrs:
        for node in soup.find_all(tag):
            src = node.get(attr)
            if not src:
                continue
            abs_url = urljoin(url, src)
            if is_resource(abs_url) or abs_url.endswith('.html') or abs_url.endswith('.htm'):
                crawl(abs_url)

if __name__ == '__main__':
    crawl(BASE_URL)
    print('全部下载完成！请在 downloaded_simulation 目录下查看。') 