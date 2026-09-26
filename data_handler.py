
import os
import json

class DataHandler:
    def __init__(self):
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Files for storing data
        self.users_file = "data/users.json"
        self.achievements_dir = "data/achievements"
        
        # Create achievements directory if it doesn't exist
        os.makedirs(self.achievements_dir, exist_ok=True)
        
        # Initialize empty data structures if files don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def load_users(self):
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_users(self, users_data):
        with open(self.users_file, 'w') as f:
            json.dump(users_data, f)
    
    def get_user_achievements_file(self, username):
        return os.path.join(self.achievements_dir, f"{username}_achievements.json")
