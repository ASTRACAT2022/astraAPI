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
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'astracat')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'v9033262')

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

**Изменения**:
- Добавлен `matplotlib.use('Agg')` для корректной работы графиков на сервере.
- Добавлена поддержка `HEAD`-запросов в маршрут `/` (Render может использовать `HEAD` для проверки).
- Логин и пароль админ-панели берутся из переменных окружения (`ADMIN_USERNAME`, `ADMIN_PASSWORD`).
- Для локального тестирования используется `host='0.0.0.0'` и порт из `$PORT` (по умолчанию 5000).

#### Шаг 2: Проверьте `requirements.txt`
Убедитесь, что в корне репозитория есть `requirements.txt` с необходимыми зависимостями:

<xaiArtifact artifact_id="65f8f516-310d-457b-af77-6932db3dad36" artifact_version_id="1b27fcbf-6ef2-4f4b-9537-aafb92c3b836" title="requirements.txt" contentType="text/plain">
```
Flask==3.0.3
matplotlib==3.9.2
gunicorn==23.0.0
```

Если вы используете Poetry, сгенерируйте `requirements.txt`:
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

#### Шаг 3: Настройте Render
1. **Build Command**:
   - Установите:
     ```
     pip install -r requirements.txt
     ```
   - Это установит зависимости из `requirements.txt`.

2. **Start Command**:
   - Установите:
     ```
     gunicorn -w 4 -b 0.0.0.0:$PORT app:app
     ```
   - Это запускает приложение через Gunicorn, привязывая его к порту, указанному в `$PORT`, и к `0.0.0.0` для внешних соединений.

3. **Environment Variables**:
   - Добавьте в Render:
     - `PYTHON_VERSION`: `3.11.11` (обычно уже установлено).
     - `ADMIN_USERNAME`: `admin` (или ваш логин).
     - `ADMIN_PASSWORD`: `password123` (или ваш пароль).

4. **Проверьте файлы**:
   - Убедитесь, что в репозитории (`https://github.com/ASTRACAT2022/astraAPI`) есть:
     - `app.py` (с обновлённым кодом).
     - `templates/admin.html` (из предыдущего ответа).
     - `requirements.txt`.
     - `vpn_keys.txt` (даже пустой, создастся автоматически при первом запуске).

#### Шаг 4: Обновите репозиторий
1. Склонируйте репозиторий локально (если ещё не сделали):
   ```bash
   git clone https://github.com/ASTRACAT2022/astraAPI
   cd astraAPI
   ```

2. Обновите `app.py` и `requirements.txt` (скопируйте код выше).
3. Добавьте или обновите `templates/admin.html` и `vpn_keys.txt`.
4. Закоммитьте изменения:
   ```bash
   git add .
   git commit -m "Исправлена привязка порта и конфигурация для Render"
   git push origin main
   ```

#### Шаг 5: Перезапустите деплой
- В панели Render выберите ваш сервис и нажмите **Redeploy**.
- Убедитесь, что используется последний коммит (не фиксированный `962d7d50`, если вы добавили изменения).

#### Шаг 6: Проверьте файлы и ключи
- **Файл `vpn_keys.txt`**:
  - Убедитесь, что он существует в репозитории или создаётся приложением.
  - Добавьте тестовые ключи, например:
    ```
    key1-abc-123
    key2-def-456
    key3-ghi-789
    ```
  - Если файл пуст, API вернёт 404 (`No keys available`), что может быть причиной ошибки в логах.

- **Права доступа**:
  - На Render файлы (`vpn_keys.txt`, `used_keys.txt`) создаются в рабочей директории. Убедитесь, что приложение имеет права на запись (по умолчанию должно работать).

#### Шаг 7: Тестирование
- **API**: Откройте `https://your-render-url.onrender.com` (или `example.com`). Должен вернуться VPN-ключ в формате RAW, например:
  ```
  key1-abc-123
  ```
- **Админ-панель**: Откройте `https://your-render-url.onrender.com/admin` (или `example.com/admin`). Введите логин `admin` и пароль `password123`. Проверьте:
  - Статистику (общее количество ключей, использованные, доступные).
  - График.
  - Форму загрузки ключей.

### Если проблема сохраняется
1. **Проверьте логи Render**:
   - После деплоя посмотрите полные логи в панели Render. Если есть ошибки, связанные с `gunicorn`, Flask или файлами, пришлите их мне.
2. **Проверьте порт**:
   - Убедитесь, что Gunicorn запускается с правильным портом. Лог `127.0.0.1` указывает, что используется неверная привязка. Gunicorn с `-b 0.0.0.0:$PORT` должен это исправить.
3. **Ошибка 404**:
   - Если запрос `HEAD /` продолжает возвращать 404, проверьте, есть ли ключи в `vpn_keys.txt`. Если файл пуст, добавьте ключи.
   - Убедитесь, что маршрут `/` обрабатывает `HEAD`-запросы (в обновлённом коде это сделано).
4. **Документация Render**:
   - Ознакомьтесь с требованиями к портам: https://render.com/docs/web-services#port-binding.
5. **Репозиторий**:
   - Если проблема в самом репозитории (например, отсутствуют файлы), проверьте содержимое коммита `962d7d50` или обновите репозиторий с новыми файлами.

### Дополнительные рекомендации
- **Постоянное хранилище**: Файлы `vpn_keys.txt` и `used_keys.txt` на Render не сохраняются между деплоями. Для сохранения данных настройте Render Disk (https://render.com/docs/disks) или используйте базу данных (например, SQLite).
- **Безопасность**: Замените `admin`/`password123` на более надёжные значения и храните их в переменных окружения.
- **Логирование**: Добавьте логирование в `app.py` для отладки:
  ```python
  import logging
  logging.basicConfig(level=logging.INFO)
  app.logger.info('Starting application...')
  ```

Если после выполнения шагов ошибка сохраняется, пришлите:
- Полные логи Render.
- Содержимое `requirements.txt`.
- Подтверждение, что `vpn_keys.txt` содержит ключи.
Я помогу разобраться!
