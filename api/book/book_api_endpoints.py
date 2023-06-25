from datetime import datetime, date
from typing import List

from fastapi import Depends, HTTPException, status
from pydantic.class_validators import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from starlette.responses import JSONResponse

from api.account.utils import get_current_user
from api.book.utils import is_book_borrowed_by_user
from enums import ActionType, RatingEnum
from models import User, Book, UserBookHistory, Category, UserBookRating
from schema import BookCreate, BookUpdate, CategoryCreate, CategoryRead, CategoryUpdate, BookRead, RatingCreate, \
    UserActivate
from settings import get_db
from fastapi import APIRouter

# router
router = APIRouter()


@router.post("/api/book", response_model=None)
async def create_book(book: BookCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    :param book: book data in request body
    :param current_user: current requested user
    :raises: if user is not admin
    :return:
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized! ADMIN can only access",
        )

    # Extract the category_id from the book_data
    category_id = book.category_id

    # Query the category with the provided category_id
    category = db.query(Category).get(category_id)

    if not category:
        # Handle the case where the category doesn't exist
        return {"status": "error", "message": "Category not found"}

    db_book = Book(title=book.title, description=book.description, author=book.author, count=book.count,
                   categories=[category])
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return {"status": "OK", "message": "Book created successfully", "Book": db_book}


@router.get("/api/books", response_model=None)
async def get_all_books(current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 10,
                        db: Session = Depends(get_db)):
    """
    :param current_user: requested user
    :param skip: omit the number of rows from beginning
    :param limit: limit the number of rows
    :raises: if user is not logged in
    :return: books
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view books!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    books = db.query(Book).offset(skip).limit(limit).all()
    return books


@router.get("/api/all-books", response_model=None)
async def get_all_books(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    :param current_user: requested user
    :raises: if user is not logged in
    :return: books
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view books!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # return books along with their category instances
    books = db.query(Book).options(joinedload(Book.categories)).all()
    return {"books": books}


@router.get("/api/book/{book_id}", response_model=None)
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
    # book along with its category
    book = db.query(Book).filter(Book.id == book_id).options(joinedload(Book.categories)).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return book


@router.put("/api/book/{book_id}", response_model=None)
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
    # find book
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    # find category
    category = db.query(Category).filter(Category.id == book_update.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    # update dict
    for key, value in book_update.dict(exclude_unset=True).items():
        setattr(book, key, value)
    book.categories = [category]  # Update the book's category
    db.commit()
    db.refresh(book)
    return {"Status": "OK", "message": "Book updated successfully", "Book": book}


@router.delete("/api/book/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    return JSONResponse({"Status": "OK", "message": "Book deleted successfully!"})


# Borrow Book
@router.post("/api/book/{book_id}/borrow", status_code=status.HTTP_204_NO_CONTENT)
async def borrow_book(book_id: int, current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
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
        history = UserBookHistory(user_id=current_user.id, book_id=book_id, borrowed_date=datetime.utcnow(),
                                  action=ActionType.BORROW)
        db.add(history)
        book.count -= 1
        db.commit()
    except Exception as e:
        print(e)
    return JSONResponse({"Status": "OK", "message": "The book was successfully borrowed"})


@router.post("/api/book/{book_id}/return", status_code=status.HTTP_204_NO_CONTENT)
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
    history.action = ActionType.RETURN
    book.count += 1
    db.commit()

    return JSONResponse({"Status": "OK", "message": "The book was successfully returned"})


@router.get("/api/user/book", response_model=None)
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


@router.get("/api/history/", response_model=None)
async def retrieve_history(
        email: Optional[str] = None,
        book_title: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        borrowed_date: Optional[date] = None,
        returned_date: Optional[date] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Retrieve book history data based on provided filters
    """

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized! Only admins can access this endpoint.",
        )

    query = db.query(UserBookHistory)

    if email:
        query = query.join(User).filter(User.email == email)

    if book_title:
        query = query.join(Book).filter(Book.title == book_title)

    if action_type:
        if action_type == ActionType.BORROW:
            query = query.filter(UserBookHistory.action == action_type)
        elif action_type == ActionType.RETURN:
            query = query.filter(UserBookHistory.action == action_type)

    if borrowed_date:
        query = query.filter(UserBookHistory.borrowed_date == borrowed_date)

    if returned_date:
        query = query.filter(UserBookHistory.returned_date == returned_date)

    book_history = query.all()
    return book_history


@router.post("/api/category", response_model=None)
def create_category(
        category: CategoryCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    :param category: category data
    :param current_user: requested user
    :raises: if user not admin
    :return: category data with success message
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can create category")

    new_category = Category(title=category.title, description=category.description)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return {"Status": "OK", "message": "The category successfully created",
            "Category": new_category}


@router.get("/api/categories", response_model=List[CategoryRead])
def read_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    :current_user: requested user
    :raises: if user not authenticated
    :return: return all categories
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view categories!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    categories = db.query(Category).all()
    return categories


@router.get("/api/category/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    :current_user: requested user
    :raises: if user not authenticated
    :return: return all categories
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view category!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not Exist")
    return category


@router.put("/api/category/{category_id}", response_model=CategoryRead)
def update_category(
        category_id: int,
        category: CategoryUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    :param category_id: int
    :param category: response schema
    :param current_user: requested user
    :raises: if user not admin or not authenticated
    :return: updated category instance
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can update category")

    existing_category = db.query(Category).get(category_id)
    if not existing_category:
        raise HTTPException(status_code=404, detail="Category not Exist")

    existing_category.title = category.title
    existing_category.description = category.description
    db.commit()
    db.refresh(existing_category)
    return existing_category


@router.delete("/api/category/{category_id}")
def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    :param category_id: int
    :param current_user: requested user
    :raises: if user not admin or not authenticated
    :return: success message
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can delete category")

    category = db.query(Category).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not Exist")

    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}


# Category search to get all books related to a category
@router.get("/api/category/{category_id}/books", response_model=List[BookRead])
def get_books_by_category(category_id: int, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    """
    :param category_id: int
    :param current_user: requested user
    :raises: if user is not authenticated
    :return: books related with the category
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view books!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    category = db.query(Category).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not exist")

    books = category.books
    return books


# Book rating by borrowed user
@router.post("/api/book/{book_id}/rating", response_model=None)
def rate_book(
        book_id: int,
        rating: RatingCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    :param book_id: int
    :param rating: int
    :param current_user: requested user
    :raieses: if user is not authenticated
    :return: success response with book data
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view books!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(rating.rating)
    print(RatingEnum)
    if rating.rating not in RatingEnum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid rating value. Allowed values: [1, 2, 3, 4, 5]",
        )

    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not is_book_borrowed_by_user(book_id, current_user.id, db):
        raise HTTPException(
            status_code=403, detail="Only borrowed users can rate books"
        )
    try:
        rating_value = RatingEnum(rating.rating)  # Convert the rating to the enum value
        print(f"RATING VALUE ======================================== {rating_value}")
        print(f"RATING VALUE ======================================== {rating_value.name}")
        print(f"RATING VALUE ======================================== {rating_value.value}")

        new_rating = UserBookRating(
            user_id=current_user.id, book_id=book_id, rating=rating_value.name
        )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid rating value provided",
        )
    except Exception as e:
        raise e
    return {
        "id": new_rating.id,
        "book_id": new_rating.book_id,
        "book_name": new_rating.book.title,
        "user_id": new_rating.user_id,
        "user_name": new_rating.user.name,
        "rating": new_rating.rating.name,
    }


# Activate/Deactivate user (admin only)
@router.put("/api/user/{user_id}/activate", response_model=None)
def activate_user(
        user_id: int,
        user_activate: UserActivate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    :param user_id: user Id
    :param current_user: requested user
    :raises: if user is not authenticated or not an admin user
    :return: success response with user data
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can activate/deactivate users")

    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = user_activate.is_active
    db.commit()
    db.refresh(user)
    if user_activate.is_active:
        msg = f"User - {user.name} activated successfully"
    else:
        msg = f"User- {user.name} Deactivated successfully"
    return {"Status": "OK", "message": msg, "User": user}


@router.get("/api/search-books", response_model=List[BookRead])
async def search_books(title: Optional[str] = None, author: Optional[str] = None, category_id: Optional[int] = None,
                       db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
                       ):
    """
    Search books by title, author, and/or category.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not Authorized to view books!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    query = db.query(Book)
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Book.author.ilike(f"%{author}%"))
    if category_id:
        query = query.join(Book.categories).filter(Category.id == category_id)
    books = query.all()
    return books
