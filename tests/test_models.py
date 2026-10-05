import pytest
from dataclasses import FrozenInstanceError
from user_registry.models import User

def test_user_creation():

    user = User(name = "Alice", email = "alice@example.com")
    assert user.name == "Alice"
    assert user.email == "alice@example.com"

def test_user_immutability():

    user = User(name = "Alice", email = "alice@example.com")

    with pytest.raises(FrozenInstanceError):
        user.name = "Bob"