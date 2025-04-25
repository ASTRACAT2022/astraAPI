```python
from flask import Flask, Response, render_template, request, redirect, url_for, flash
import random
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Файлы для ключей
KEYS_FILE = 'vpn_keys.txt'
USED_KEYS_FILE = 'used_keys.txt'

# Авторизация админ-панели
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password123')

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

# Чтение ключей из файла
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

# API для выдачи ключа
@app.route('/', methods=['GET', 'HEAD'])
def get_vpn_key():
    keys = read_keys()
    used_keys = read_used_keys()
    available_keys = [key for key in keys if key not in used_keys]
    
    if not available_keys:
        return Response('No keys available', mimetype='text/plain', status=404)
    
    if request.method == 'HEAD':
        return Response(status=200)
    
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

    if request.method == 'POST':
        if 'keys' in request.form:
            new_keys = request.form['keys'].splitlines()
            new_keys = [key.strip() for key in new_keys if key.strip()]
            with open(KEYS_FILE, 'a') as f:
                for key in new_keys:
                    f.write(key + '\n')
            flash('Keys uploaded successfully!')
            return redirect(url_for('admin_panel'))

    return render_template('admin.html', 
                         total_keys=total_keys, 
                         used_keys=used_count, 
                         available_keys=available_count)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
```

#### `admin.html`
<xaiArtifact artifact_id="7d9d9352-7aa1-4357-9212-18d71d2dc2b1" artifact_version_id="30d7a4f9-c711-49ab-828e-39e7b026d8fd" title="templates/admin.html" contentType="text/html">
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VPN Keys Admin Panel</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: auto; }
        .stats { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .stats div { padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
        .form-container { margin-top: 20px; }
        textarea { width: 100%; height: 200px; }
        button { padding: 10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #45a049; }
        .flash { color: green; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>VPN Keys Admin Panel</h1>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="flash">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="stats">
            <div>Total Keys: {{ total_keys }}</div>
            <div>Used Keys: {{ used_keys }}</div>
            <div>Available Keys: {{ available_keys }}</div>
        </div>

        <div class="form-container">
            <h3>Upload New VPN Keys</h3>
            <form method="POST">
                <textarea name="keys" placeholder="Enter VPN keys (one per line)"></textarea>
                <br>
                <button type="submit">Upload Keys</button>
            </form>
        </div>
    </div>
</body>
</html>
```

#### `requirements.txt`
<xaiArtifact artifact_id="6747138e-bae0-43bd-9a3b-c3ed8254f741" artifact_version_id="f5d79666-b2d8-4bc3-a384-3e11a851e627" title="requirements.txt" contentType="text/plain">
```
Flask==3.0.3
gunicorn==23.0.0
```

#### Настройка Render
1. **Build Command**:
   ```
   pip install -r requirements.txt
   ```

2. **Start Command**:
   ```
   gunicorn -w 4 -b 0.0.0.0:$PORT app:app
   ```

3. **Environment Variables**:
   - `PYTHON_VERSION`: `3.11.11`
   - `ADMIN_USERNAME`: `admin`
   - `ADMIN_PASSWORD`: `password123`

4. **Файлы в репозитории**:
   - `app.py` (в корне)
   - `templates/admin.html` (в папке `templates/`)
   - `requirements.txt` (в корне)
   - `vpn_keys.txt` (в корне, с тестовыми ключами, например):
     ```
     key1-abc-123
     key2-def-456
     key3-ghi-789
     ```

#### Обновление репозитория
1. Склонируйте:
   ```bash
   git clone https://github.com/ASTRACAT2022/astraAPI
   cd astraAPI
   ```

2. Замените `app.py`, `templates/admin.html`, `requirements.txt`.
3. Обновите `vpn_keys.txt`.
4. Закоммитьте:
   ```bash
   git add .
   git commit -m "Минимальный код API без инструкций"
   git push origin main
   ```

#### Перезапуск деплоя
- В Render нажмите **Redeploy** с последним коммитом.

#### Тестирование
- **API**: `https://your-render-url.onrender.com` → ключ, например `key1-abc-123`.
- **Админ-панель**: `https://your-render-url.onrender.com/admin` → логин `admin`, пароль `password123`, проверьте статистику и загрузку ключей.

Если ошибка сохраняется, пришлите:
- Логи Render.
- Содержимое `app.py` (чтобы проверить отсутствие лишнего текста).
- Подтверждение, что `vpn_keys.txt` содержит ключи и `templates/admin.html` есть.
