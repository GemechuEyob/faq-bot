import json
import os

from dotenv import load_dotenv
from openai import api_key
from pydantic_settings import BaseSettings

load_dotenv()
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]
API_KEYS = os.environ["API_KEYS"]


class Settings(BaseSettings):
    database_url: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}?sslmode=disable"
    api_keys: list | str = API_KEYS
    scrape_interval_hours: int = 24
    browser_headless: bool = True
    max_concurrent_scrapes: int = 3
    scrape_timeout_seconds: int = 140
    log_level: str = "INFO"
    similarity_threshold: float = 0.85
    vector_dimension: int = 384
    respect_robots_txt: bool = True

    def __init__(self):
        super().__init__()
        # Check if api_keys is a string and parse it
        if isinstance(self.api_keys, str):
            self.api_keys = json.loads(self.api_keys)


settings = Settings()
