from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vpn_keys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Модель для хранения VPN ключей
class VPNKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(500), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    use_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)

    def __repr__(self):
        return f'<VPNKey {self.key}>'

# Создаем базу данных при первом запуске
with app.app_context():
    db.create_all()

# API endpoint для получения ключа
@app.route('/')
def get_vpn_key():
    # Ищем неиспользованный ключ
    unused_key = VPNKey.query.filter_by(is_used=False).first()
    
    if unused_key:
        # Помечаем как использованный
        unused_key.is_used = True
        unused_key.use_count += 1
        unused_key.last_used = db.func.now()
        db.session.commit()
        
        # Возвращаем ключ в RAW формате
        return unused_key.key, 200, {'Content-Type': 'text/plain'}
    else:
        return "No VPN keys available", 404

# Админ панель
@app.route('/admin')
def admin_panel():
    # Получаем статистику
    total_keys = VPNKey.query.count()
    used_keys = VPNKey.query.filter_by(is_used=True).count()
    unused_keys = total_keys - used_keys
    
    # Получаем список всех ключей
    keys = VPNKey.query.all()
    
    return render_template('admin.html', 
                         total_keys=total_keys,
                         used_keys=used_keys,
                         unused_keys=unused_keys,
                         keys=keys)

# Добавление новых ключей
@app.route('/admin/add', methods=['POST'])
def add_keys():
    keys_text = request.form.get('keys')
    if keys_text:
        keys_list = keys_text.split('\n')
        for key in keys_list:
            if key.strip():
                new_key = VPNKey(key=key.strip())
                db.session.add(new_key)
        db.session.commit()
    return redirect(url_for('admin_panel'))

# Сброс ключа
@app.route('/admin/reset/<int:key_id>')
def reset_key(key_id):
    key = VPNKey.query.get(key_id)
    if key:
        key.is_used = False
        db.session.commit()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
