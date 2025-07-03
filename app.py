from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import json
from werkzeug.utils import secure_filename
import shutil
from bs4 import BeautifulSoup
import requests
import time
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 请替换为更安全的密钥

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 简单用户模型
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# 仅支持一个管理员用户
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'  # 请修改为更安全的密码

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return User(user_id)
    return None

# 游戏信息存储文件
games_file = 'games.json'
if not os.path.exists(games_file):
    with open(games_file, 'w') as f:
        json.dump([], f)

def load_games():
    with open(games_file, 'r') as f:
        return json.load(f)

def save_games(games):
    with open(games_file, 'w') as f:
        json.dump(games, f, ensure_ascii=False, indent=2)

UPLOAD_HTML_DIR = os.path.join('static', 'uploads', 'html')
UPLOAD_IMG_DIR = os.path.join('static', 'uploads', 'images')
os.makedirs(UPLOAD_HTML_DIR, exist_ok=True)
os.makedirs(UPLOAD_IMG_DIR, exist_ok=True)

@app.route('/')
def index():
    games = load_games()
    return render_template('index.html', games=games)

@app.route('/game/<int:game_id>')
def game(game_id):
    games = load_games()
    game = next((g for g in games if g['id'] == game_id), None)
    if not game:
        return '游戏未找到', 404
    html_path = game['html_path'].lstrip('/')
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 替换常规路径
        content = content.replace('./电场模拟_files/', '/static/uploads/html/电场模拟_files/')
        content = content.replace('src="电场模拟_files/', 'src="/static/uploads/html/电场模拟_files/')
        content = content.replace('href="电场模拟_files/', 'href="/static/uploads/html/电场模拟_files/')
        # 替换裸文件名（如 src="1.png"、src="p5.min.js" 等）
        content = re.sub(r'src="([a-zA-Z0-9_\-]+\.(png|jpg|jpeg|svg|gif|js|css|html))"', r'src="/static/uploads/html/电场模拟_files/\1"', content)
        content = re.sub(r'href="([a-zA-Z0-9_\-]+\.(css|js|svg))"', r'href="/static/uploads/html/电场模拟_files/\1"', content)
        return Response(content, mimetype='text/html')
    except Exception as e:
        return f'加载游戏失败: {e}', 500

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    games = load_games()
    return render_template('admin.html', games=games)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            user = User(username)
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('用户名或密码错误')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/upload', methods=['POST'])
@login_required
def upload_game():
    name = request.form['name']
    desc = request.form['desc']
    thumbnail = request.files['thumbnail']
    html_file = request.files['html_file']
    # 保存缩略图
    thumb_filename = secure_filename(thumbnail.filename)
    thumb_path = os.path.join(UPLOAD_IMG_DIR, thumb_filename)
    thumbnail.save(thumb_path)
    # 保存HTML文件
    html_filename = secure_filename(html_file.filename)
    html_path = os.path.join(UPLOAD_HTML_DIR, html_filename)
    html_file.save(html_path)
    # 生成新游戏ID
    games = load_games()
    new_id = (max([g['id'] for g in games]) + 1) if games else 1
    # 构建新游戏信息
    game = {
        'id': new_id,
        'name': name,
        'desc': desc,
        'thumbnail': f'/static/uploads/images/{thumb_filename}',
        'html_path': f'/static/uploads/html/{html_filename}'
    }
    games.append(game)
    save_games(games)
    flash('上传成功！')
    return redirect(url_for('admin'))

def crawl_simulation(url, save_dir):
    # 简化版爬虫，只下载主页面和所有资源
    visited = set()
    RESOURCE_EXTS = ['.js', '.css', '.png', '.jpg', '.jpeg', '.svg', '.gif', '.ico', '.json', '.html', '.htm', '.webp']
    def safe_filename(url):
        from urllib.parse import urlparse
        path = urlparse(url).path.lstrip('/')
        return os.path.join(save_dir, path)
    def is_resource(url):
        return any(url.lower().endswith(ext) for ext in RESOURCE_EXTS)
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
            return local_path
        except Exception as e:
            print(f'下载失败: {url}，原因: {e}')
            return None
    def crawl(url):
        if url in visited:
            return
        visited.add(url)
        local_path = download_file(url)
        if not local_path or not (url.endswith('.html') or url.endswith('.htm')):
            return
        with open(local_path, 'r', encoding="utf-8", errors='ignore') as f:
            soup = BeautifulSoup(f, 'html.parser')
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
                from urllib.parse import urljoin
                abs_url = urljoin(url, src)
                if is_resource(abs_url) or abs_url.endswith('.html') or abs_url.endswith('.htm'):
                    crawl(abs_url)
    crawl(url)

def fix_html_paths(html_file):
    from bs4 import BeautifulSoup
    with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f, 'html.parser')
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
            # 修正以 /、icons/、images/ 开头的路径
            if src.startswith('/'):
                node[attr] = '.' + src
            elif src.startswith('icons/') or src.startswith('images/'):
                node[attr] = './' + src
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))

@app.route('/admin/crawl', methods=['POST'])
@login_required
def admin_crawl():
    url = request.form['url']
    name = request.form['name']
    desc = request.form['desc']
    thumbnail = request.files['thumbnail']
    # 生成保存目录
    folder_name = f"game_{int(time.time())}"
    save_dir = os.path.join('static', 'uploads', 'html', folder_name)
    os.makedirs(save_dir, exist_ok=True)
    # 保存缩略图
    thumb_filename = secure_filename(thumbnail.filename)
    thumb_path = os.path.join('static', 'uploads', 'images', thumb_filename)
    thumbnail.save(thumb_path)
    # 爬取资源
    crawl_simulation(url, save_dir)
    # 主入口HTML路径
    html_path = os.path.join('/static/uploads/html', folder_name, 'simulation.html')
    # 自动修正 simulation.html 资源路径
    fix_html_paths(os.path.join(save_dir, 'simulation.html'))
    # 生成新游戏ID
    games = load_games()
    new_id = (max([g['id'] for g in games]) + 1) if games else 1
    game = {
        'id': new_id,
        'name': name,
        'desc': desc,
        'thumbnail': f'/static/uploads/images/{thumb_filename}',
        'html_path': html_path
    }
    games.append(game)
    save_games(games)
    flash('爬取并集成成功！')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:game_id>', methods=['POST'])
@login_required
def delete_game(game_id):
    games = load_games()
    game = next((g for g in games if g['id'] == game_id), None)
    if not game:
        flash('未找到该游戏')
        return redirect(url_for('admin'))
    # 删除html文件
    html_path = game.get('html_path', '').lstrip('/')
    if html_path and os.path.exists(html_path):
        try:
            if os.path.isdir(html_path):
                shutil.rmtree(html_path)
            else:
                os.remove(html_path)
        except Exception as e:
            print(f'删除HTML文件失败: {e}')
    # 删除缩略图
    thumbnail_path = game.get('thumbnail', '').lstrip('/')
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            os.remove(thumbnail_path)
        except Exception as e:
            print(f'删除缩略图失败: {e}')
    # 移除games.json中的数据
    games = [g for g in games if g['id'] != game_id]
    save_games(games)
    flash('删除成功！')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True) 