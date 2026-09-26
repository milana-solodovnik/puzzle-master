
import json
from models import Achievement

class AchievementManager:
    def __init__(self):
        self.achievements = {}

    def get_achievement(self, user_id):
        return self.achievements.get(user_id)

    def update_achievement(self, user_id, achievement):
        self.achievements[user_id] = achievement
        return True
