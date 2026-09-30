import pytest
from user_registry.models import User
from user_registry.repository import UserRepositry

def test_repository_add_and_list():
    repo = UserRepositry()
    user = User(name="Alice", email="alice@example.com")

    repo.add(user)
    users = repo.list_all()

    assert len(users) == 1
    assert users[0].name == "Alice"
    assert users[0].email == "alice@example.com"

def test_repository_protects_internal_list():

    repo = UserRepositry()
    user1 = User(name="Alice", email= "alice@example.com")
    repo.add(user1)

    users = repo.list_all()
    users.append(User(name = "Bob", email="bob@example.com"))

    internal_users = repo.list_all()
    assert len(internal_users) == 1
    assert internal_users[0].name == "Alice"