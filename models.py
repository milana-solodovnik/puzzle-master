
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    achievements = db.relationship('Achievement', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_data = db.Column(db.Text, default='{}')
    completed_puzzles = db.Column(db.Integer, default=0)
    available_images = db.Column(db.Text, default='["puzzle1"]')
    best_times = db.Column(db.Text, default='{}')

    def __init__(self, user):
        self.user = user
        self.achievement_data = '{}'
        self.completed_puzzles = 0
        self.available_images = '["puzzle1"]'
        self.best_times = '{}'

    def get_achievements(self):
        return json.loads(self.achievement_data)

    def get_available_images(self):
        return json.loads(self.available_images)

    def get_best_times(self):
        return json.loads(self.best_times)

    def update_best_time(self, difficulty, time):
        times = json.loads(self.best_times)
        if difficulty not in times or time < float(times[difficulty]):
            times[difficulty] = time
            self.best_times = json.dumps(times)
            return True
        return False

    def update_after_puzzle_completion(self, time, difficulty):
        self.completed_puzzles += 1
        self.update_best_time(difficulty, time)
        
        achievements = json.loads(self.achievement_data)
        available_images = json.loads(self.available_images)
        
        if self.completed_puzzles == 1 and not achievements.get('first_puzzle'):
            achievements['first_puzzle'] = True
            if "puzzle2" not in available_images:
                available_images.append("puzzle2")
        
        if self.completed_puzzles >= 5 and not achievements.get('five_puzzles'):
            achievements['five_puzzles'] = True
            if "puzzle3" not in available_images:
                available_images.append("puzzle3")
            if "puzzle4" not in available_images:
                available_images.append("puzzle4")
        
        if difficulty == "4x4" and time < 30 and not achievements.get('speed_master'):
            achievements['speed_master'] = True
            if "puzzle5" not in available_images:
                available_images.append("puzzle5")
        
        self.achievement_data = json.dumps(achievements)
        self.available_images = json.dumps(available_images)
