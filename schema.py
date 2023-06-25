from pydantic import BaseModel
from pydantic.class_validators import Optional
from datetime import date

from enums import RatingEnum


class UserCreate(BaseModel):
    """
    User registration request model schema
    """
    name: str
    email: str
    password: str


class UserOut(BaseModel):
    """
    User response model schema
    """
    id: int
    name: str
    email: str



class UserLogin(BaseModel):
    """
    User login request model schema
    """
    email: str
    password: str


class Token(BaseModel):
    """
    Token response model schema
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Token data model schema
    """
    user_id: Optional[int] = None


# Create Book (Admin Only)
class BookCreate(BaseModel):
    """
    Book creation request model schema
    """
    title: str
    description: str
    author: str
    count: int
    category_id:int

class BookOut(BaseModel):
    """
    Book response model for listing all books schema
    """
    id: int
    title: str
    description: str
    author: str
    count: int


# Update Book (Admin Only)
class BookUpdate(BaseModel):
    """
    Book update request model schema
    """
    title: Optional[str]
    description: Optional[str]
    author: Optional[str]
    count: Optional[int]
    category_id:int


class UserBookHistorySchema(BaseModel):
    """
    User book history response model schema
    """
    id: int
    user_id: int
    book_id: int
    borrowed_date: date
    returned_date: date

    class Config:
        orm_mode = True

# Category Schemas
class CategoryBase(BaseModel):
    title: str
    description: str


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int

    class Config:
        orm_mode = True


class CategoryUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]


# Book Schemas
class BookBase(BaseModel):
    title: str
    description: str
    author: str
    count: int


class BookRead(BookBase):
    id: int

    class Config:
        orm_mode = True


# Rating Schema
class RatingCreate(BaseModel):
    rating: RatingEnum


# User Activation Schema
class UserActivate(BaseModel):
    is_active: bool