from typing import List
from .models import User
from .repository import UserRepositry

class UserService:
    def __init__(self, repositry: UserRepositry):

        self._repositry = repositry

    def add_user(self, name:str, email:str)-> User:

        normalized_name = name.strip()
        normalized_email = email.strip().lower()

        if not normalized_name:
            raise ValueError("Name cannot be empty")

        if "@" not in normalized_email:
            raise ValueError("Email must contain '@'")

        user = User(name=normalized_name, email= normalized_email)
        self._repositry.add(user)

        return user

    def list_users(self)-> List[User]:
        return self._repositry.list_all()