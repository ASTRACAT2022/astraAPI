```python
from flask import Flask, Response, render_template, request, redirect, url_for, flash
import random
import os
from functools import wraps
import matplotlib
matplotlib.use('Agg')  # Для серверного рендеринга графиков
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Для флеш-сообщений

# Файлы для хранения ключей
KEYS_FILE = 'vpn_keys.txt'
USED_KEYS_FILE = 'used_keys.txt'

# Простая авторизация
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password123')

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
@app.route('/', methods=['GET', 'HEAD'])
def get_vpn_key():
    keys = read_keys()
    used_keys = read_used_keys()
    available_keys = [key for key in keys if key not in used_keys]
    
    if not available_keys:
        return Response('No keys available', mimetype='text/plain', status=404)
    
    if request.method == 'HEAD':
        return Response(status=200)  # Ответ на HEAD-запрос
    
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
    # Для локального тестирования, не используется на Render
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
```

**Что исправлено**:
- Удалены Markdown-теги (```````python` и ```````).
- Сохранена поддержка `HEAD`-запросов для проверок Render.
- Используется `matplotlib.use('Agg')` для графиков.
- Логин и пароль берутся из переменных окружения.

#### Шаг 2: Проверьте `requirements.txt`
Убедитесь, что в корне репозитория есть `requirements.txt` с необходимыми зависимостями:

<xaiArtifact artifact_id="3803d098-b753-4cf3-a45c-d89174723a45" artifact_version_id="ee333b04-8d24-4902-8356-99fd9b1e545c" title="requirements.txt" contentType="text/plain">
```
Flask==3.0.3
matplotlib==3.9.2
gunicorn==23.0.0
```

Если файл отсутствует, создайте его с указанным содержимым.

#### Шаг 3: Обновите настройки Render
1. **Build Command**:
   - Убедитесь, что установлено:
     ```
     pip install -r requirements.txt
     ```
   - Это установит зависимости из `requirements.txt`.

2. **Start Command**:
   - Измените на:
     ```
     gunicorn -w 4 -b 0.0.0.0:$PORT app:app
     ```
   - Это запускает приложение через Gunicorn, привязывая его к порту `$PORT` и интерфейсу `0.0.0.0`.

3. **Environment Variables**:
   - Добавьте в Render:
     - `PYTHON_VERSION`: `3.11.11` (обычно установлено по умолчанию).
     - `ADMIN_USERNAME`: `admin` (или ваш логин).
     - `ADMIN_PASSWORD`: `password123` (или ваш пароль).

4. **Проверьте файлы в репозитории**:
   - Убедитесь, что в `https://github.com/ASTRACAT2022/astraAPI` есть:
     - `app.py` (с кодом выше).
     - `templates/admin.html` (из предыдущих ответов).
     - `requirements.txt` (как указано выше).
     - `vpn_keys.txt` (даже пустой, он создастся автоматически).

#### Шаг 4: Обновите репозиторий
1. Склонируйте репозиторий (если ещё не сделали):
   ```bash
   git clone https://github.com/ASTRACAT2022/astraAPI
   cd astraAPI
   ```

2. Замените `app.py` на код выше.
3. Убедитесь, что `requirements.txt` и `templates/admin.html` присутствуют.
4. Создайте или обновите `vpn_keys.txt` с тестовыми ключами, например:
   ```
   key1-abc-123
   key2-def-456
   key3-ghi-789
   ```
5. Закоммитьте и отправьте изменения:
   ```bash
   git add .
   git commit -m "Исправлен app.py, удалены Markdown-теги, настроен Gunicorn"
   git push origin main
   ```

#### Шаг 5: Перезапустите деплой
- В панели Render выберите ваш сервис и нажмите **Redeploy**.
- Убедитесь, что деплой использует последний коммит.

#### Шаг 6: Тестирование
- **API**: Откройте `https://your-render-url.onrender.com` (или `example.com`). Должен вернуться VPN-ключ в формате RAW, например:
  ```
  key1-abc-123
  ```
- **Админ-панель**: Откройте `https://your-render-url.onrender.com/admin` (или `example.com/admin`). Введите логин `admin` и пароль `password123`. Проверьте:
  - Статистику (общее количество ключей, использованные, доступные).
  - График.
  - Форму для загрузки ключей.

### Если проблема сохраняется
1. **Проверьте логи Render**:
   - После деплоя посмотрите логи в панели Render. Если есть другие ошибки, пришлите их.
2. **Проверьте `app.py`**:
   - Откройте `app.py` в редакторе и убедитесь, что первая строка — это `from flask import ...`, а не ```````python`.
   - Убедитесь, что файл не содержит других Markdown-тегов или текста инструкций.
3. **Проверьте команду запуска**:
   - Убедитесь, что Render использует `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`, а не `python app.py`.
4. **Проверьте `vpn_keys.txt`**:
   - Если файл пуст, API вернёт 404. Добавьте тестовые ключи, как указано выше.
5. **Файлы в репозитории**:
   - Проверьте содержимое репозитория на GitHub. Убедитесь, что все файлы (`app.py`, `requirements.txt`, `templates/admin.html`, `vpn_keys.txt`) присутствуют и актуальны.

### Дополнительные рекомендации
- **Постоянное хранилище**: Файлы `vpn_keys.txt` и `used_keys.txt` не сохраняются между деплоями на Render. Для сохранения данных настройте Render Disk (https://render.com/docs/disks) или используйте базу данных (например, SQLite).
- **Безопасность**: Замените `admin`/`password123` на болееSyndrome: invalid syntax
- **Логирование**: Добавьте логирование в `app.py` для отладки:
  ```python
  import logging
  logging.basicConfig(level=logging.INFO)
  app.logger.info('Starting application...')
  ```

Если после выполнения шагов ошибка сохраняется, пришлите:
- Полные логи Render.
- Содержимое вашего текущего `app.py` (чтобы проверить, нет ли там лишнего текста).
- Подтверждение, что `vpn_keys.txt` содержит ключи.
Я помогу разобраться!
