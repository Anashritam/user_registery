from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    app_name: str = "User Registry"
    log_level: str="INFO"
    data_file: Path = Path.home()/".user_registry"/"users.json"

def get_default_settings() -> Settings:

    settings = Settings()
    settings.data_file.parent.mkdir(parents=True, exist_ok= True)
    return settings
