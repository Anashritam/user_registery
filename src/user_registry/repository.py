import json
from typing import List
from .models import User
from .config import get_data_file_path

class UserRepository:
    """JSON file based storage for User Objects."""
    def __init__(self):
        self._file_path=get_data_file_path()
        self._users:List[User]= self._load_users()

    def _load_users(self)-> List[User]:
        if not self._file_path.exists():
            return []
        try:
            with open(self._file_path, "r") as file:
                data = json.load(file)

                return [User(name=user["name"], email=user["email"]) for user in data]
        except (json.JSONDecodeError, KeyError):
            return []

    def _save_users(self)-> None:

        with open(self._file_path, "w") as file:
            user_dicts= [{"name": user.name, "email":user.email} for user in self._users]
            json.dump(user_dicts, file, indent = 2)

    def add(self, user: User)-> None:
        self._users.append(user)
        self._save_users()

    def list_all(self)-> List[User]:

        return list(self._users)


    