
from werkzeug.security import generate_password_hash, check_password_hash

class UserManager:
    def __init__(self):
        self.users = {}
    
    def add_user(self, username, password):
        if username in self.users:
            return False
        
        password_hash = generate_password_hash(password)
        self.users[username] = {
            'password_hash': password_hash
        }
        return True
    
    def verify_user(self, username, password):
        if username not in self.users:
            return False
        
        return check_password_hash(self.users[username]['password_hash'], password)
