from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import json
from werkzeug.utils import secure_filename
import shutil
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
    if not os.path.exists(html_path):
        return f'HTML文件不存在: {html_path}', 404

    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 获取HTML文件所在的目录
        html_dir = os.path.dirname(html_path)
        html_filename = os.path.basename(html_path)

        # 动态处理资源文件路径
        # 1. 处理相对路径的资源文件 (不以 http/https 或 / 开头)
        # 确保只修改真正的相对路径，忽略外部链接和根路径绝对路径
        content = re.sub(r'src="((?!https?://)(?!/)[^"]*\.(png|jpg|jpeg|svg|gif|js|css|html))"',
                         lambda m: f'src="/{html_dir}/{m.group(1)}"', content)
        content = re.sub(r'href="((?!https?://)(?!/)[^"]*\.(css|js|svg))"',
                         lambda m: f'href="/{html_dir}/{m.group(1)}"', content)

        # 2. 处理特定文件夹的资源（如电场模拟_files）
        # 检查是否存在对应的资源文件夹
        possible_resource_dirs = [
            os.path.join(html_dir, '电场模拟_files'),
            os.path.join(html_dir, html_filename.replace('.html', '_files')),
            os.path.join(html_dir, 'files'),
            os.path.join(html_dir, 'assets')
        ]

        for resource_dir in possible_resource_dirs:
            if os.path.exists(resource_dir):
                dir_name = os.path.basename(resource_dir)
                # 替换该文件夹下的资源路径
                # 注意：这里也需要确保替换的源路径是相对的，而不是外部URL
                # 假设这些路径本身就是相对的，并且不会与外部URL冲突
                content = content.replace(f'./{dir_name}/', f'/{resource_dir}/')
                content = content.replace(f'src="{dir_name}/', f'src="/{resource_dir}/')
                content = content.replace(f'href="{dir_name}/', f'href="/{resource_dir}/')
                break

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


@app.route('/admin/edit/<int:game_id>', methods=['POST'])
@login_required
def edit_game(game_id):
    name = request.form.get('name', '').strip()
    desc = request.form.get('desc', '').strip()
    games = load_games()
    updated = False
    for g in games:
        if g['id'] == game_id:
            g['name'] = name
            g['desc'] = desc
            updated = True
            break
    if updated:
        save_games(games)
        flash('修改成功！')
    else:
        flash('未找到该游戏')
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)