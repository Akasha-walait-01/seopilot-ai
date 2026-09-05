# This file sets up the database connection using SQLAlchemy
# We are using SQLite for now (simple file-based database)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import settings

# create the database engine
# connect_args is needed only for sqlite
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# session factory, used to talk to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# base class that all our database models will inherit from
Base = declarative_base()


def get_db():
    # this function gives a database session to each request
    # and closes it automatically when done
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()