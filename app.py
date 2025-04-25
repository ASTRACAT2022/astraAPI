from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS  # Добавлено для CORS
from datetime import datetime
import os

# Инициализация приложения с явным указанием папки шаблонов
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vpn_keys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Включение CORS для API (разрешить запросы с https://vpngen.vercel.app)
CORS(app, resources={r"/": {"origins": "https://vpngen.vercel.app"}})

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Модель VPN ключа
class VPNKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(500), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    use_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание базы данных и администратора по умолчанию
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()

# API для получения ключа
@app.route('/')
def get_vpn_key():
    active_key = VPNKey.query.filter_by(is_active=True, is_used=False).first()
    if active_key:
        active_key.is_used = True
        active_key.use_count += 1
        active_key.last_used = datetime.utcnow()
        db.session.commit()
        return active_key.key, 200, {'Content-Type': 'text/plain'}
    return "No VPN keys available", 404

# Аутентификация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Админ-панель
@app.route('/admin')
@login_required
def admin_dashboard():
    stats = {
        'total': VPNKey.query.count(),
        'active': VPNKey.query.filter_by(is_active=True).count(),
        'used': VPNKey.query.filter_by(is_used=True).count(),
        'available': VPNKey.query.filter_by(is_used=False, is_active=True).count()
    }
    keys = VPNKey.query.order_by(VPNKey.created_at.desc()).all()
    return render_template('admin/dashboard.html', stats=stats, keys=keys)

# Управление ключами
@app.route('/admin/key/add', methods=['POST'])
@login_required
def add_key():
    keys_text = request.form.get('keys')
    if keys_text:
        keys_list = [k.strip() for k in keys_text.split('\n') if k.strip()]
        for key in keys_list:
            if not VPNKey.query.filter_by(key=key).first():
                new_key = VPNKey(key=key, notes=request.form.get('notes'))
                db.session.add(new_key)
        db.session.commit()
        flash(f'Добавлено {len(keys_list)} ключей', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/key/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_key(id):
    key = VPNKey.query.get_or_404(id)
    if request.method == 'POST':
        key.key = request.form['key']
        key.notes = request.form['notes']
        key.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Ключ успешно обновлён', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_key.html', key=key)

@app.route('/admin/key/delete/<int:id>')
@login_required
def delete_key(id):
    key = VPNKey.query.get_or_404(id)
    db.session.delete(key)
    db.session.commit()
    flash('Ключ успешно удалён', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/key/reset/<int:id>')
@login_required
def reset_key(id):
    key = VPNKey.query.get_or_404(id)
    key.is_used = False
    key.use_count = 0
    db.session.commit()
    flash('Ключ успешно сброшен', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
