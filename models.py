import enum

from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, create_engine, Table
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Enum as SQLAlchemyEnum

from settings import engine

Base = declarative_base()


class ActionType(str, enum.Enum):
    """
    Enum for BookActionType
    """
    BORROW = "BORROW"
    RETURN = "RETURN"


class RatingEnum(enum.Enum):
    ONE_STAR = 1
    TWO_STARS = 2
    THREE_STARS = 3
    FOUR_STARS = 4
    FIVE_STARS = 5

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
    is_active = Column(Boolean, default=False)

    # Relationship with UserBookHistory model
    book_history = relationship("UserBookHistory", back_populates="user")
    book_ratings = relationship("UserBookRating", back_populates="user")

association_table = Table('association', Base.metadata,
    Column('category_id', Integer, ForeignKey('categories.id')),
    Column('book_id', Integer, ForeignKey('books.id'))
)

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)

    books = relationship("Book", secondary=association_table, back_populates="categories")


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
    categories = relationship("Category", secondary=association_table, back_populates="books")
    user_ratings = relationship("UserBookRating", back_populates="book")



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

class UserBookRating(Base):
    """
    UserBookRating model representing the 'user_book_rating' table in the database
    """
    __tablename__ = "user_book_rating"


    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    rating = Column(SQLAlchemyEnum(RatingEnum))

    # relationships with User and Book models
    user = relationship("User", back_populates="book_ratings")
    book = relationship("Book", back_populates="user_ratings")



# Create tables in the database
Base.metadata.create_all(engine)
