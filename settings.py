import os
from databases import Database
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

# Database Configuration from environment variables
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT', "5432")

# Set up the database connection URL using environment variables
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
database = Database(DATABASE_URL)

# Create a SQLAlchemy engine for database operations
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class for getting a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Authentication Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_db() -> Session:
    """
    Dependency function to get a database session.
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


# Dependency: Get Database Connection
async def get_database():
    """
    Dependency function to get a database connection.
    """
    # Connect to the database
    await database.connect()
    try:
        yield database
    finally:
        await database.disconnect()
