import json
import logging
from typing import List
from pathlib import Path
from .models import User

logger = logging.getLogger(__name__)

class UserRepository:
    """JSON file based storage for User Objects."""
    def __init__(self, data_file: Path):
        self._file_path=data_file
        self._file_path.parent.mkdir(parents=True, exist_ok= True)
        self._users:List[User]= self._load_users()

    def _load_users(self) -> List[User]:
        """Private method to read users from the JSON file."""
        # 1. Missing file is fine (first run). Return empty list.
        if not self._file_path.exists():
            return []
        
        try:
            with open(self._file_path, "r") as file:
                data = json.load(file)
                return [User(name=user["name"], email=user["email"]) for user in data]
                
        except json.JSONDecodeError as exc:
            # 2. Malformed JSON is a corruption issue.
            raise DataCorruptionError(f"Invalid JSON format in {self._file_path}") from exc
            
        except KeyError as exc:
            # 3. Missing fields in JSON is also corruption.
            raise DataCorruptionError(f"Missing required field in {self._file_path}: {exc}") from exc
            
        except (PermissionError, OSError) as exc:
            # 4. Filesystem access failures.
            raise StorageError(f"Cannot read from {self._file_path}: {exc}") from exc

    def _save_users(self)-> None:

        try: 
            with open(self._file_path, "w") as file:
                user_dicts = [{"name": user.name, "email":user.email} for user in self._users]
                json.dump(user_dicts, file, indent = 2)
        except IOError as e:
            logger.error(f"Failed to save users to {self._file_path}: {e}.")

    def add(self, user: User)-> None:
        self._users.append(user)
        self._save_users()

    def list_all(self)-> List[User]:

        return list(self._users)


    