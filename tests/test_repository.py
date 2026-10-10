import pytest
from pathlib import Path
import tempfile
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

# def test_add_rollback_on_save_failure(tmp_path: Path, monkeypatch):
#     """Verify rollback and exception chaining using a deterministic mock."""
#     data_file = tmp_path / "users.json"
#     data_file.write_text("[]")
#     repo = UserRepository(data_file)
#     user = User(name="Alice", email="alice@example.com")
    
#     # Mock builtins.open to fail ONLY on write operations ('w')
#     original_open = open
#     def fail_open(*args, **kwargs):
#         if len(args) > 1 and 'w' in args[1]:
#             raise PermissionError("Simulated write failure")
#         return original_open(*args, **kwargs)
    
#     monkeypatch.setattr("builtins.open", fail_open)
    
#     with pytest.raises(StorageError) as exc_info:
#         repo.add(user)
        
#     # Verify the original OS error is preserved
#     assert isinstance(exc_info.value.__cause__, PermissionError)
    
#     # Verify the in-memory state was rolled back
#     assert repo.list_all() == []

def test_load_users_missing_key_raises_corruption(tmp_path: Path):
    """A record missing the 'email' key must raise DataCorruptionError."""
    data_file = tmp_path / "missing_key.json"
    data_file.write_text('[{"name": "Alice"}]')
    with pytest.raises(DataCorruptionError, match="missing 'name' or 'email' keys"):
        UserRepository(data_file)

def test_load_users_null_record_raises_corruption(tmp_path: Path):
    """A null (None) record in the list must raise DataCorruptionError."""
    data_file = tmp_path / "null_record.json"
    data_file.write_text('[null]')
    with pytest.raises(DataCorruptionError, match="is not a dictionary"):
        UserRepository(data_file)

def test_load_users_invalid_name_type_raises_corruption(tmp_path: Path):
    """A record with a non-string 'name' must raise DataCorruptionError."""
    data_file = tmp_path / "invalid_type.json"
    data_file.write_text('[{"name": 123, "email": "a@example.com"}]')
    with pytest.raises(DataCorruptionError, match="invalid types"):
        UserRepository(data_file)

def test_add_rollback_on_save_failure(tmp_path: Path, monkeypatch):
    """Verify rollback and exception chaining using a deterministic mock."""
    data_file = tmp_path / "users.json"
    data_file.write_text("[]")
    repo = UserRepository(data_file)
    user = User(name="Alice", email="alice@example.com")
    
    # Mock tempfile.NamedTemporaryFile to fail during write
    original_tempfile = tempfile.NamedTemporaryFile
    
    def fail_tempfile(*args, **kwargs):
        # Create the temp file object first
        temp_file = original_tempfile(*args, **kwargs)
        # Then mock its write method to fail
        original_write = temp_file.write
        def failing_write(data):
            raise PermissionError("Simulated disk full")
        temp_file.write = failing_write
        return temp_file
    
    monkeypatch.setattr("tempfile.NamedTemporaryFile", fail_tempfile)
    
    with pytest.raises(StorageError) as exc_info:
        repo.add(user)
        
    # Verify the original OS error is preserved
    assert isinstance(exc_info.value.__cause__, PermissionError)
    
    # Verify the in-memory state was rolled back
    assert repo.list_all() == []


def test_atomic_write_preserves_original_on_failure(tmp_path: Path, monkeypatch):
    """Verify that a failed write leaves the original JSON file completely intact."""
    
    # 1. Setup: Alice is already saved on disk
    data_file = tmp_path / "users.json"
    original_content = '[{"name": "Alice", "email": "alice@example.com"}]'
    data_file.write_text(original_content)
    
    repo = UserRepository(data_file)
    bob = User(name="Bob", email="bob@example.com")
    
    # 2. Mock tempfile.NamedTemporaryFile to fail during write
    original_tempfile = tempfile.NamedTemporaryFile
    
    def fail_tempfile(*args, **kwargs):
        temp_file = original_tempfile(*args, **kwargs)
        original_write = temp_file.write
        def failing_write(data):
            raise PermissionError("Simulated disk full on temp file")
        temp_file.write = failing_write
        return temp_file
        
    monkeypatch.setattr("tempfile.NamedTemporaryFile", fail_tempfile)
    
    # 3. Action: Try to add Bob (this should fail during the .tmp write)
    with pytest.raises(StorageError) as exc_info:
        repo.add(bob)
        
    assert isinstance(exc_info.value.__cause__, PermissionError)
    
    # 4. Assert In-memory state is unchanged (Bob was never added)
    assert len(repo.list_all()) == 1
    assert repo.list_all()[0].name == "Alice"
    
    # 5. Assert Disk state is unchanged (The original file was never truncated!)
    assert data_file.read_text() == original_content