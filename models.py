from enum import Enum

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, create_engine
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Enum as SQLAlchemyEnum

from enums import ActionType
from settings import engine

Base = declarative_base()


class ActionType(str, Enum):
    """
    Enum for BookActionType
    """
    BORROW = "BORROW"
    RETURN = "RETURN"


class User(Base):
    """
    User model representing the 'users' table in the database
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_admin = Column(Boolean, default=False)

    # Relationship with UserBookHistory model
    book_history = relationship("UserBookHistory", back_populates="user")


class Book(Base):
    """
    Book model representing the 'books' table in the database
    """
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    author = Column(String)
    count = Column(Integer)

    # Relationship with UserBookHistory model
    user_history = relationship("UserBookHistory", back_populates="book")


class UserBookHistory(Base):
    """
    UserBookHistory model representing the 'user_book_history' table in the database
    """
    __tablename__ = "user_book_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    borrowed_date = Column(Date)
    returned_date = Column(Date)
    action = Column(SQLAlchemyEnum(ActionType, name="action_type"))

    # relationships with User and Book models
    user = relationship("User", back_populates="book_history")
    book = relationship("Book", back_populates="user_history")


# Create tables in the database
Base.metadata.create_all(engine)
