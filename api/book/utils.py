from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import UserBookHistory


def is_book_borrowed_by_user(book_id: int, user_id: int, db: Session):
    # Check if the book is borrowed by the user
    is_borrowed = db.query(UserBookHistory).filter_by(book_id=book_id, user_id=user_id, returned_date=None).first()

    if not is_borrowed:
        raise HTTPException(status_code=404, detail="Book is not borrowed by the user")

    return True