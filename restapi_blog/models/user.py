from datetime import datetime
from typing import Dict

users_db: Dict[int, "User"] = {}
next_user_id = 1


class User:
    def __init__(self, email: str, login: str, password: str):
        global next_user_id

        self.id = next_user_id
        self.email = email
        self.login = login
        self.password = password
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        next_user_id += 1
