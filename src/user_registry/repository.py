from typing import List
from .models import User

class UserRepositry:
    def __init__(self):
        self._users: List[User] = []

    def add(self, user:User)-> None:
        self._users.append(user)

    def list_all(self)-> List(User):
        return list(self._users)