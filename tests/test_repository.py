import pytest
from pathlib import Path
from user_registry.models import User
from user_registry.repository import UserRepository
from user_registry.exceptions import DataCorruptionError, StorageError

def test_load_users_missing_file_returns_empty(tmp_path: Path):
    data_file = tmp_path / "missing.json"
    repo = UserRepository(data_file)
    assert repo.list_all() == []

def test_load_users_malformed_json_raises_corruption(tmp_path: Path):
    data_file = tmp_path / "bad.json"
    data_file.write_text("{ this is not valid json }")
    with pytest.raises(DataCorruptionError):
        UserRepository(data_file)

def test_load_users_root_not_list_raises_corruption(tmp_path: Path):
    data_file = tmp_path / "dict_root.json"
    data_file.write_text('{"name": "Alice", "email": "alice@example.com"}')
    with pytest.raises(DataCorruptionError, match="Root JSON element must be a list"):
        UserRepository(data_file)

def test_load_users_invalid_types_raises_corruption(tmp_path: Path):
    data_file = tmp_path / "invalid_types.json"
    data_file.write_text('[{"name": "Alice", "email": 123}]')
    with pytest.raises(DataCorruptionError, match="invalid types"):
        UserRepository(data_file)

def test_load_users_directory_path_raises_storage_error(tmp_path: Path):
    # Renamed: This fails during __init__ (loading), not during save.
    with pytest.raises(StorageError):
        UserRepository(tmp_path)

def test_add_rollback_on_save_failure(tmp_path: Path, monkeypatch):
    """Verify rollback and exception chaining using a deterministic mock."""
    data_file = tmp_path / "users.json"
    data_file.write_text("[]")
    repo = UserRepository(data_file)
    user = User(name="Alice", email="alice@example.com")
    
    # Mock builtins.open to fail ONLY on write operations ('w')
    original_open = open
    def fail_open(*args, **kwargs):
        if len(args) > 1 and 'w' in args[1]:
            raise PermissionError("Simulated write failure")
        return original_open(*args, **kwargs)
    
    monkeypatch.setattr("builtins.open", fail_open)
    
    with pytest.raises(StorageError) as exc_info:
        repo.add(user)
        
    # Verify the original OS error is preserved
    assert isinstance(exc_info.value.__cause__, PermissionError)
    
    # Verify the in-memory state was rolled back
    assert repo.list_all() == []