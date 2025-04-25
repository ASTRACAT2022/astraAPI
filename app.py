from flask import Flask, Response, render_template, request, redirect, url_for, flash
import random
import os
from functools import wraps
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Для флеш-сообщений

# Файлы для хранения ключей
KEYS_FILE = 'vpn_keys.txt'
USED_KEYS_FILE = 'used_keys.txt'

# Простая авторизация
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

# Проверка авторизации
def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated_function

# Чтение ключей
def read_keys():
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, 'w') as f:
            f.write('')
        return []
    with open(KEYS_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Чтение использованных ключей
def read_used_keys():
    if not os.path.exists(USED_KEYS_FILE):
        with open(USED_KEYS_FILE, 'w') as f:
            f.write('')
        return []
    with open(USED_KEYS_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Сохранение использованного ключа
def save_used_key(key):
    with open(USED_KEYS_FILE, 'a') as f:
        f.write(key + '\n')

# API для получения ключа
@app.route('/')
def get_vpn_key():
    keys = read_keys()
    used_keys = read_used_keys()
    available_keys = [key for key in keys if key not in used_keys]
    
    if not available_keys:
        return Response('No keys available', mimetype='text/plain', status=404)
    
    key = random.choice(available_keys)
    save_used_key(key)
    return Response(key, mimetype='text/plain')

# Админ-панель
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    keys = read_keys()
    used_keys = read_used_keys()
    total_keys = len(keys)
    used_count = len(used_keys)
    available_count = total_keys - used_count

    # Обработка загрузки ключей
    if request.method == 'POST':
        if 'keys' in request.form:
            new_keys = request.form['keys'].splitlines()
            new_keys = [key.strip() for key in new_keys if key.strip()]
            with open(KEYS_FILE, 'a') as f:
                for key in new_keys:
                    f.write(key + '\n')
            flash('Keys uploaded successfully!')
            return redirect(url_for('admin_panel'))

    # Генерация графика
    plt.figure(figsize=(6, 4))
    plt.bar(['Total', 'Used', 'Available'], [total_keys, used_count, available_count], color=['#4CAF50', '#FF5733', '#00C4B4'])
    plt.title('VPN Keys Statistics')
    plt.ylabel('Count')
    
    # Сохранение графика в base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()

    return render_template('admin.html', 
                         total_keys=total_keys, 
                         used_keys=used_count, 
                         available_keys=available_count,
                         chart_img=img_base64)

if __name__ == '__main__':
    app.run(debug=True)
