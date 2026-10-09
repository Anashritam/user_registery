class UserRegistryError(Exception):
    """Base exception for all User Registry application errors."""
    pass

class RepositoryError(UserRegistryError):
    """Base exception for all data storage and retrieval errors."""
    pass

class DataCorruptionError(RepositoryError):
    """Raised when stored data is malformed, invalid JSON, or missing required fields."""
    pass

class StorageError(RepositoryError):
    """Raised when the system cannot read from or write to the storage medium."""
    pass