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
        self._file_path = data_file
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        self._users: List[User] = self._load_users()

    def _load_users(self) -> List[User]:
        if not self._file_path.exists():
            return []
            
        try:
            with open(self._file_path, "r") as file:
                data = json.load(file)
                
                # 1. Root must be a list
                if not isinstance(data, list):
                    raise DataCorruptionError("Root JSON element must be a list.")
                
                # 2. Validate each record's structure and types
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        raise DataCorruptionError(f"Record at index {i} is not a dictionary.")
                    if "name" not in item or "email" not in item:
                        raise DataCorruptionError(f"Record at index {i} is missing 'name' or 'email' keys.")
                    if not isinstance(item["name"], str) or not isinstance(item["email"], str):
                        raise DataCorruptionError(
                            f"Record at index {i} has invalid types for 'name' or 'email' (must be strings)."
                        )
                
                # If validation passes, safely construct User objects
                return [User(name=user["name"], email=user["email"]) for user in data]
                
        except json.JSONDecodeError as e:
            raise DataCorruptionError(f"Invalid JSON in {self._file_path}: {e}") from e
        except DataCorruptionError:
            # Re-raise our specific corruption errors directly
            raise
        except (PermissionError, OSError) as e:
            raise StorageError(f"Failed to read from {self._file_path}: {e}") from e

    def _save_users(self) -> None:
        try:
            with open(self._file_path, "w") as file:
                user_dicts = [{"name": user.name, "email": user.email} for user in self._users]
                json.dump(user_dicts, file, indent=2)
        except OSError as exc:
            raise StorageError(f"Failed to save users to {self._file_path}") from exc

    def add(self, user: User) -> None:
        previous_length = len(self._users)
        try:
            self._users.append(user)
            self._save_users()
        except StorageError:
            # Rollback: truncate the list back to its exact previous length
            del self._users[previous_length:]
            raise

    def list_all(self) -> List[User]:
        return list(self._users)