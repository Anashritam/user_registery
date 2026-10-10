import json
import logging
from typing import List
from pathlib import Path
from .models import User
from .exceptions import DataCorruptionError, StorageError


logger = logging.getLogger(__name__)

class UserRepository:
    """JSON file based storage for User Objects."""
    def __init__(self, data_file: Path):
        self._file_path=data_file
        self._file_path.parent.mkdir(parents=True, exist_ok= True)
        self._users:List[User]= self._load_users()

    def _load_users(self) -> List[User]:
        # 1. Missing file is expected on first run -> return empty list
        if not self._file_path.exists():
            return []
            
        try:
            with open(self._file_path, "r") as file:
                data = json.load(file)
                return [User(name=user["name"], email=user["email"]) for user in data]
                
        except (json.JSONDecodeError, KeyError) as e:
            # 2. Malformed JSON or missing keys -> DO NOT return []. Raise explicitly.
            raise DataCorruptionError(
                f"Failed to load users from {self._file_path}: {e}"
            ) from e
            
        except (PermissionError, OSError) as e:
            # 3. Filesystem access failure -> Raise StorageError
            raise StorageError(
                f"Failed to read from {self._file_path}: {e}"
            ) from e

    def _save_users(self) -> None:
        try:
            with open(self._file_path, "w") as file:
                user_dicts = [
                    {"name": user.name, "email": user.email}
                    for user in self._users
                ]
                json.dump(user_dicts, file, indent=2)
        except OSError as exc:
            raise StorageError(
                f"Failed to save users to {self._file_path}"
            ) from exc

    def add(self, user: User) -> None:
        # Save the exact state before mutation
        previous_length = len(self._users)
        
        try:
            self._users.append(user)
            self._save_users()
        except StorageError:
            # Rollback: truncate the list back to its exact previous length
            del self._users[previous_length:]
            raise

    def list_all(self)-> List[User]:

        return list(self._users)


    