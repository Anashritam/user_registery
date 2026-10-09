import pytest
from pathlib import Path
from user_registry.models import User
from user_registry.repository import UserRepository
from user_registry.exceptions import DataCorruptionError, StorageError

def test_load_users_missing_file_returns_empty(tmp_path: Path):
    """A missing file should safely return an empty list (first-run behavior)."""
    data_file = tmp_path / "missing.json"
    repo = UserRepository(data_file)
    assert repo.list_all() == []

def test_load_users_malformed_json_raises_corruption(tmp_path: Path):
    """Invalid JSON should raise DataCorruptionError, not return an empty list."""
    data_file = tmp_path / "bad.json"
    data_file.write_text("{ this is not valid json }")
    
    with pytest.raises(DataCorruptionError):
        UserRepository(data_file)

def test_load_users_missing_keys_raises_corruption(tmp_path: Path):
    """Valid JSON but missing required fields should raise DataCorruptionError."""
    data_file = tmp_path / "missing_keys.json"
    # Missing the "email" key
    data_file.write_text('[{"name": "Alice"}]') 
    
    with pytest.raises(DataCorruptionError):
        UserRepository(data_file)

def test_save_users_directory_path_raises_storage_error(tmp_path: Path):
    """Passing a directory instead of a file path should raise StorageError."""
    # tmp_path is a directory. If we use it as the file path, writing will fail.
    with pytest.raises(StorageError):
        repo = UserRepository(tmp_path)
        repo.add(User(name="Alice", email="alice@example.com"))