import argparse
import sys
import logging
from .config import get_default_settings
from .logging_config import configure_logging
from .repository import UserRepository
from .services import UserService
from .exceptions import RepositoryError

def main():
    settings = get_default_settings()
    configure_logging(settings)

    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="User Registry CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    add_parser = subparsers.add_parser("add", help="Add a new user")
    add_parser.add_argument("name", type=str, help="User's name")
    add_parser.add_argument("email", type=str, help="User's email")
    
    subparsers.add_parser("list", help="List all users")

    args = parser.parse_args()

    # Wrap the repository initialization and execution to catch storage/schema errors
    try:
        repo = UserRepository(data_file=settings.data_file)
        service = UserService(repo)

        if args.command == "add":
            try:
                user = service.add_user(args.name, args.email)
                print(f"User created:\n{user.name} <{user.email}>")
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        elif args.command == "list":
            users = service.list_users()

            if not users:
                print("No users found.")
            else:
                for user in users:
                    print(f"{user.name} <{user.email}>")

        else: 
            parser.print_help()
            sys.exit(1)

    except RepositoryError as e:
        # Catch DataCorruptionError or StorageError and handle gracefully
        logger.error(f"Repository error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()