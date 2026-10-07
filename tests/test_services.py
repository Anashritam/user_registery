import pytest
from pathlib import Path
from user_registry.models import User
from user_registry.repository import UserRepository
from user_registry.services import UserService

@pytest.fixture
def service(tmp_path: Path):
    test_file = tmp_path/ "test_users.json"
    repo = UserRepository(data_file=test_file)
    return UserService(repo)

def test_add_user_valid_and_normalized(service):
    user = service.add_user("Alice", "ALICE@EXAMPLE.COM")
    assert user.name == "Alice"
    assert user.email == "alice@example.com"

def test_add_user_empty_name_raises_error(service):

    with pytest.raises(ValueError, match = "Name cannot be empty"):
        service.add_user(" ","alice@example.com")

    with pytest.raises(ValueError, match="Name cannot be empty"):
        service.add_user("", "alice@example.com")

def test_add_user_invalid_email_raises_error(service):
    with pytest.raises(ValueError, match = "Email must contain '@'"):
        service.add_user("Alice","aliceexample.com")

def test_list_users(service):
    service.add_user("Alice", "alice@example.com")
    service.add_user("Bob", "bob@example.com")

    users=service.list_users()
    assert len(users)== 2
    assert users[0].name == "Alice"
    assert users[1].name == "Bob"