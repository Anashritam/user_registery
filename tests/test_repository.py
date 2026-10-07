import pytest
from pathlib import Path
from user_registry.models import User
from user_registry.repository import UserRepository

def test_repository_add_and_list(tmp_path: Path):
    test_flie = tmp_path/"test_users.json"
    repo = UserRepository(data_file=test_flie)

    user =User(name= "Alice", email="alice@example.com")
    repo.add(user)

    new_repo = UserRepository(data_file=test_flie)
    users=new_repo.list_all()

    assert len(users) ==1
    assert users[0].name == "Alice"

def test_repository_protects_internal_list(tmp_path: Path):
    test_file = tmp_path/"test_users.json"
    repo = UserRepository(data_file=test_file)
    user1 = User(name ="Alice", email="alice@example.com")
    repo.add(user1)

    users = repo.list_all()
    users.append(User(name="Bob", email="bob@example.com"))

    internal_users = repo.list_all()
    assert len(internal_users) == 1
    assert internal_users[0].name == "Alice"