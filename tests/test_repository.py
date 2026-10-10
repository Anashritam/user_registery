import pytest
import tempfile
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

def test_load_users_missing_keys_raises_corruption(tmp_path: Path):
    data_file = tmp_path / "missing_keys.json"
    data_file.write_text('[{"name": "Alice"}]')
    with pytest.raises(DataCorruptionError, match="missing"):
        UserRepository(data_file)

def test_load_users_non_dict_record_raises_corruption(tmp_path: Path):
    data_file = tmp_path / "non_dict.json"
    data_file.write_text("[null]")
    with pytest.raises(DataCorruptionError, match="not a dictionary"):
        UserRepository(data_file)

def test_load_users_directory_path_raises_storage_error(tmp_path: Path):
    with pytest.raises(StorageError):
        UserRepository(tmp_path)

# --- ISSUE B: Partial Write Failure Test ---
def test_atomic_write_partial_write_failure(tmp_path: Path, monkeypatch):
    """Simulate a partial write failure. Verify original file is intact and temp file is cleaned up."""
    data_file = tmp_path / "users.json"
    original_content = '[{"name": "Alice", "email": "alice@example.com"}]'
    data_file.write_text(original_content)
    
    repo = UserRepository(data_file)
    bob = User(name="Bob", email="bob@example.com")
    
    original_tempfile = tempfile.NamedTemporaryFile
    
    def partial_write_tempfile(*args, **kwargs):
        temp_file = original_tempfile(*args, **kwargs)
        original_write = temp_file.write
        write_count = 0
        
        def failing_write(data):
            nonlocal write_count
            write_count += 1
            # Fail on the second write attempt to simulate a partial write
            if write_count > 1:
                raise OSError("Simulated partial disk failure")
            return original_write(data)
            
        temp_file.write = failing_write
        return temp_file
        
    monkeypatch.setattr("tempfile.NamedTemporaryFile", partial_write_tempfile)
    
    with pytest.raises(StorageError) as exc_info:
        repo.add(bob)
        
    assert isinstance(exc_info.value.__cause__, OSError)
    
    # In-memory state unchanged
    assert len(repo.list_all()) == 1
    assert repo.list_all()[0].name == "Alice"
    
    # Original disk file unchanged
    assert data_file.read_text() == original_content
    
    # Temp file was cleaned up
    assert len(list(tmp_path.glob("*.tmp"))) == 0


# --- ISSUE C: Replace Failure Test ---
def test_atomic_write_replace_failure(tmp_path: Path, monkeypatch):
    """Simulate Path.replace failing. Verify original file is intact, memory unchanged, and temp cleaned up."""
    data_file = tmp_path / "users.json"
    original_content = '[{"name": "Alice", "email": "alice@example.com"}]'
    data_file.write_text(original_content)
    
    repo = UserRepository(data_file)
    bob = User(name="Bob", email="bob@example.com")
    
    original_replace = Path.replace
    
    def failing_replace(self, target):
        raise OSError("Simulated replace failure (e.g., cross-device link or permissions)")
        
    monkeypatch.setattr("pathlib.Path.replace", failing_replace)
    
    with pytest.raises(StorageError) as exc_info:
        repo.add(bob)
        
    assert isinstance(exc_info.value.__cause__, OSError)
    
    # In-memory state unchanged
    assert len(repo.list_all()) == 1
    assert repo.list_all()[0].name == "Alice"
    
    # Original disk file unchanged
    assert data_file.read_text() == original_content
    
    # Temp file was cleaned up by the except block
    assert len(list(tmp_path.glob("*.tmp"))) == 0

def test_add_does_not_update_memory_on_save_failure(tmp_path: Path, monkeypatch):
    """Verify that self._users is not updated if _save_users fails."""
    data_file = tmp_path / "users.json"
    data_file.write_text("[]")
    
    repo = UserRepository(data_file)
    user = User(name="Alice", email="alice@example.com")
    
    # Mock replace to fail
    original_replace = Path.replace
    def failing_replace(self, target):
        raise OSError("Simulated replace failure")
    monkeypatch.setattr("pathlib.Path.replace", failing_replace)
    
    # Should raise StorageError
    with pytest.raises(StorageError):
        repo.add(user)
    
    # Memory should NOT have been updated
    assert len(repo.list_all()) == 0
    assert user not in repo.list_all()