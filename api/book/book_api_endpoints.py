from datetime import datetime, date

from fastapi import Depends, HTTPException, status
from pydantic.class_validators import Optional
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from api.account.utils import get_current_user
from enums import ActionType
from models import User, Book, UserBookHistory
from schema import BookCreate, BookUpdate
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
    db_book = Book(title=book.title, description=book.description, author=book.author, count=book.count)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


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
    books = db.query(Book).all()
    return books


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
    book = db.query(Book).filter(Book.id == book_id).first()
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
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    for key, value in book_update.dict(exclude_unset=True).items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


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
    history.action=ActionType.RETURN
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
