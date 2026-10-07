from pathlib import Path

APP_DIR = Path.home()/".user_registry"
DATA_FILE = APP_DIR/"users.json"

def get_data_file_path()->Path:
    APP_DIR.mkdir(exist_ok= True)
    return DATA_FILE