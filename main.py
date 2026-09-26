
import os
import secrets
import random
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from models import db, User, Achievement

# Инициализация Flask приложения
app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)
app.secret_key = "ThIsIsAsEcReTkEyFoRpUzZlEaPpLiCaTiOn"

# Настройка подключения к базе данных
# Проверяем, есть ли переменная среды DATABASE_URL (для Replit)
# Если нет, используем локальную SQLite базу данных
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///puzzle_game.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Инициализация базы данных
db.init_app(app)

# Создание таблиц при первом запуске
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main_menu'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error='Пожалуйста, введите имя пользователя и пароль')

        user = User.query.filter_by(username=username).first()

        if user and user.verify_password(password):
            session['user_id'] = user.id
            session['username'] = username
            return redirect(url_for('main_menu'))
        else:
            return render_template('login.html', error='Неверное имя пользователя или пароль')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('register.html', error='Пожалуйста, введите имя пользователя и пароль')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Такое имя пользователя уже существует')

        # Создание нового пользователя
        new_user = User(username=username, password=password)
        # Создание записи о достижениях
        new_achievement = Achievement(user=new_user)

        db.session.add(new_user)
        db.session.add(new_achievement)
        db.session.commit()

        return render_template('login.html', success='Регистрация прошла успешно! Теперь вы можете войти.')

    return render_template('register.html')

@app.route('/main_menu')
def main_menu():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('main_menu.html', username=session['username'])

@app.route('/difficulty')
def difficulty():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('difficulty.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/play')
def play():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    difficulty = request.args.get('difficulty', '2x2')

    # Получаем пользователя из базы данных
    user = User.query.get(session['user_id'])
    if not user or not user.achievements:
        return redirect(url_for('login'))

    # Используем puzzle1 как базовое изображение
    image_name = 'puzzle1'

    # Проверяем доступные изображения
    available_images = user.achievements.get_available_images()
    if available_images and len(available_images) > 0:
        image_name = random.choice(available_images)

    return render_template('game.html', difficulty=difficulty, image_name=image_name)

@app.route('/complete_puzzle', methods=['POST'])
def complete_puzzle():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Не авторизован'})

    data = request.get_json()
    time_taken = data.get('time')
    difficulty = data.get('difficulty')

    if not time_taken or not difficulty:
        return jsonify({'status': 'error', 'message': 'Недостаточно данных'})

    # Получаем пользователя и его достижения
    user = User.query.get(session['user_id'])
    if not user or not user.achievements:
        return jsonify({'status': 'error', 'message': 'Пользователь не найден'})

    # Получаем предыдущее лучшее время
    previous_best = user.achievements.get_best_times().get(difficulty, float('inf'))

    # Обновляем достижения
    user.achievements.update_after_puzzle_completion(float(time_taken), difficulty)
    
    # Сохраняем изменения в БД
    db.session.commit()

    # Проверяем, является ли это новым рекордом
    is_new_record = float(time_taken) < previous_best

    return jsonify({
        'status': 'success',
        'is_new_record': is_new_record,
        'previous_best': previous_best if previous_best < float('inf') else None,
        'achievements': user.achievements.get_achievements()
    })

@app.route('/achievements')
def achievements():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Получаем пользователя и его достижения
    user = User.query.get(session['user_id'])
    if not user or not user.achievements:
        return redirect(url_for('login'))

    achievements = user.achievements.get_achievements()
    best_times = user.achievements.get_best_times()

    return render_template('achievements.html', 
                        achievements=achievements, 
                        best_times=best_times)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Получаем пользователя
    user = User.query.get(session['user_id'])
    if user:
        db.session.delete(user)
        db.session.commit()

    session.pop('user_id', None)
    session.pop('username', None)

    return redirect(url_for('login'))

@app.route('/puzzle_image/<path:image_name>')
def puzzle_image(image_name):
    # Список возможных путей для поиска изображения
    possible_paths = [
        os.path.join('static', f"{image_name}.jpg"),
        os.path.join('PuzzleMaster', 'static', f"{image_name}.jpg"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', f"{image_name}.jpg"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', f"{image_name}.jpg")
    ]
    
    # Проверяем каждый возможный путь
    for path in possible_paths:
        if os.path.exists(path):
            return send_file(path, mimetype='image/jpeg')
    
    # Дополнительная отладочная информация при отсутствии изображения
    print(f"Не удалось найти изображение: {image_name}")
    print(f"Искали в путях: {possible_paths}")
    
    # Если изображение не найдено, возвращаем ошибку 404
    return f"Изображение {image_name} не найдено. Проверенные пути: {possible_paths}", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
