
from sqlmodel import SQLModel, create_engine, Session
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import AnyHttpUrl

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./app.db"
    CORS_ORIGINS: List[AnyHttpUrl] | List[str] = []
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

def init_db():
    from app import models  # ensure models are imported
    SQLModel.metadata.create_all(engine)

def get_db():
    with Session(engine) as session:
        yield session
        
def get_session():
    with Session(engine) as session:
        yield session
