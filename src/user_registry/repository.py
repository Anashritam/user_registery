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

    def _save_users(self, data: List[dict]) -> None:
        # 1. Define a temporary file in the SAME directory
        temp_path = self._file_path.with_suffix(".tmp")
        
        try:
            # 2. Write JSON to the temporary file
            with open(temp_path, "w") as file:
                json.dump(data, file, indent=2)
                
            # 3. Atomically replace the original file with the temporary file
            temp_path.replace(self._file_path)
            
        except OSError as exc:
            # Clean up the temp file if it was created but failed to replace
            if temp_path.exists():
                temp_path.unlink()
            raise StorageError(
                f"Failed to save users to {self._file_path}"
            ) from exc

    def add(self, user: User) -> None:
        # 1. Build the new user data in memory (DO NOT mutate self._users yet)
        user_dicts = [
            {"name": u.name, "email": u.email} for u in self._users
        ]
        user_dicts.append({"name": user.name, "email": user.email})

        # 2 & 3. Persist the data atomically (writes to temp, then replaces)
        self._save_users(user_dicts)

        # 4. Commit the in-memory change ONLY after persistence succeeds
        self._users.append(user)

    def list_all(self) -> List[User]:
        return list(self._users)