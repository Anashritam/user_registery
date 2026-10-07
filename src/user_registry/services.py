from typing import List
from .models import User
from .repository import UserRepository
import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, repository: UserRepository)->None:

        self._repository = repository

    def add_user(self, name:str, email:str)-> User:

        normalized_name = name.strip()
        normalized_email = email.strip().lower()

        if not normalized_name:
            logger.warning("Failed to create user: Empty name provided.")
            raise ValueError("Name cannot be empty")

        if "@" not in normalized_email:
            logger.warning(f"Failed to create user: Invalid email '{email}'.")
            raise ValueError("Email must contain '@'")

        user = User(name=normalized_name, email= normalized_email)
        self._repository.add(user)

        logger.info(f"Successfully created user: {user.name} <{user.email}>")

        return user

    def list_users(self)-> List[User]:

        users= self._repository.list_all()
        logger.info(f"Retrieved {len(users)} user(s) from the repository.")
        return users

    