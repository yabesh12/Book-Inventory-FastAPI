import os
import random
import string
from typing import List
from datetime import date
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic.class_validators import Optional
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from databases import Database
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel
from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum

class ActionType(str, Enum):
    BORROW = "BORROW"
    RETURN = "RETURN"



# Dependency: Get DB Session
from starlette.responses import JSONResponse


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


# Database Configuration
DB_NAME=os.environ.get('DB_NAME')
DB_USER=os.environ.get('DB_USER')
DB_PASSWORD=os.environ.get('DB_PASSWORD')
DB_HOST=os.environ.get('DB_HOST')
DB_PORT=os.environ.get('DB_PORT', "5432")

# DATABASE_URL = "postgresql://user:password@localhost:5432/db_name"
# DATABASE_URL = "sqlite:///./database.db"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# DATABASE_URL = "postgresql://book_inventoryUser:book_inventoryPassword@db:5432/book_inventory"
database = Database(DATABASE_URL)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI App
app = FastAPI()

# Models
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_admin = Column(Boolean, default=False)

    # Relationship with UserBookHistory model
    book_history = relationship("UserBookHistory", back_populates="user")


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    author = Column(String)
    count = Column(Integer)

    # Relationship with UserBookHistory model
    user_history = relationship("UserBookHistory", back_populates="book")


class UserBookHistory(Base):
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

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

async def get_user(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except InvalidTokenError:
        raise credentials_exception
    user = await get_user(db, token_data.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You are not authenticated!")
    print(f"PRINTED THE CURRENT USER {user}")
    print(type(user))
    return user


# Dependency: Get Database Connection
async def get_database():
    await database.connect()
    try:
        yield database
    finally:
        await database.disconnect()


# Password Hashing
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# User Registration
class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str


@app.post("/api/user/register", response_model=UserCreate)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    :param user: name, email, password
    :raises: if username exist
    :return: user data
    """
    user_obj = db.query(User).filter(User.email == user.email).first()
    try:
        if user_obj is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email is already exist!")
        hashed_password = get_password_hash(user.password)
        new_user = User(name=user.name, email=user.email, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        raise (e)
    return new_user.__dict__


# User Login
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


async def authenticate_user(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/api/user/login", response_model=Token)
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    """
    :param user: email, password
    :raises: if user not registered
    :return: access token
    """
    user_obj = db.query(User).filter(User.email == user.email).first()
    if user_obj is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user_obj.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# Create Book (Admin Only)
class BookCreate(BaseModel):
    title: str
    description: str
    author: str
    count: int


@app.post("/api/book", response_model=None)
async def create_book(book: BookCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized! ADMIN can only access",
        )
    db_book = Book(title=book.title, description=book.description, author=book.author, count=book.count)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


# Get All Books
class BookOut(BaseModel):
    id: int
    title: str
    description: str
    author: str
    count: int


# @app.get("/api/book", response_model=List[BookOut])
# async def get_all_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
#     books = db.query(Book).offset(skip).limit(limit).all()
#     return books


@app.get("/api/book", response_model=None)
async def get_all_books(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view books!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    books = db.query(Book).all()
    return books


@app.get("/api/book/{book_id}", response_model=None)
async def get_book(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    :param: book_id (int)
    :raises: if user not authenticated or invalid book id
    :return: single book data
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view book!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


# Update Book (Admin Only)
class BookUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    author: Optional[str]
    count: Optional[int]


@app.put("/api/book/{book_id}", response_model=None)
async def update_book(book_id: int, book_update: BookUpdate, current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """
    :param: book_id, fields to be updated given in request body
    :raises: if user is not admin
    :return: book data
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized! ADMIN can only access",
        )
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    for key, value in book_update.dict(exclude_unset=True).items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


@app.delete("/api/book/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    :param: book_id
    :raises: if book not exists
    :return: success response
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized! ADMIN can only access",
        )
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    db.delete(book)
    db.commit()
    return JSONResponse({"Status":"OK", "message":"Book deleted successfully!"})


# Borrow Book
@app.post("/api/book/{book_id}/borrow", status_code=status.HTTP_204_NO_CONTENT)
async def borrow_book(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    :param: book_id
    :raises: if book not exists or book not available
    :return: success response
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    if book.count <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is not available for borrowing")
    try:
        history = UserBookHistory(user_id=current_user.id, book_id=book_id, borrowed_date=datetime.utcnow())
        db.add(history)
        book.count -= 1
        db.commit()
        db.refresh()
    except Exception as e:
        print(e)
    return JSONResponse({"Status":"OK", "message":"The book was successfully borrowed"})


@app.post("/api/book/{book_id}/return", status_code=status.HTTP_204_NO_CONTENT)
async def return_book(book_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    :param: book_id
    :raises: if book not found or book is not borrowed already
    :return: success response
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    history = db.query(UserBookHistory).filter(
        UserBookHistory.user_id == current_user.id,
        UserBookHistory.book_id == book_id,
        UserBookHistory.returned_date.is_(None),
    ).first()
    if not history:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book is not borrowed by the user")
    history.returned_date = datetime.utcnow()
    book.count += 1
    db.commit()
    db.refresh()

    return JSONResponse({"Status":"OK", "message":"The book was successfully returned"})


@app.get("/api/user/book", response_model=None)
async def get_books_borrowed_by_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    :param: current requested user
    :return: books list borrowed by the user
    """
    history = db.query(UserBookHistory).filter(
        UserBookHistory.user_id == current_user.id,
        UserBookHistory.returned_date.is_(None),
    ).all()
    book_ids = [h.book_id for h in history]
    books = db.query(Book).filter(Book.id.in_(book_ids)).all()
    return books


class UserBookHistorySchema(BaseModel):
    id: int
    user_id: int
    book_id: int
    borrowed_date: date
    returned_date: date

    class Config:
        orm_mode = True


@app.get("/api/history", response_model=None)
async def retrieve_history(email: Optional[str] = None, book_title: Optional[str] = None, type: Optional[str] = None,
                           date: Optional[date] = None, current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """
    :param email: user email
    :param book_title: the book's title
    :param type: denotes borrow or return
    :param date: optional mentioned date
    :param current_user: current requested user
    :raises: if user is not admin
    :return: Book History data
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized! ADMIN can only access",
        )
    query = db.query(UserBookHistory)
    if email:
        query = query.join(User).filter(User.email == email)
    if book_title:
        query = query.join(Book).filter(Book.title == book_title)
    if type:
        if type == "borrow":
            query.filter(UserBookHistory.returned_date.is_(None))
        elif type == "return":
            query.filter(UserBookHistory.returned_date.isnot(None))
    if date:
        query.filter(UserBookHistory.borrowed_date >= date)
    history = query.all()
    return history
