import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get DATABASE_URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./secure_bank.db")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Function to create tables
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    return True

# Function to get a database session
def get_session():
    with Session(engine) as session:
        yield session 