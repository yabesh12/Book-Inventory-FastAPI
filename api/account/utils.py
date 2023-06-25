import jwt
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from models import User
from schema import TokenData
from settings import SECRET_KEY, ALGORITHM, oauth2_scheme, get_db
from datetime import datetime, timedelta
from pydantic.class_validators import Optional
import re


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def validate_email(email):
    """
    :param email: user email address
    :raises: if email is not valid
    :return: True
    """
    # Regular expression pattern for email validation
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    # Check if the email matches the pattern
    if not re.match(pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email address.")
    return True


def verify_password(plain_password, hashed_password):
    """
    verify password
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Password Hashing
    """
    return pwd_context.hash(password)


async def get_user(db: Session, user_id: int) -> User:
    """
    return the user from user_id
    """
    return db.query(User).filter(User.id == user_id).first()


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    :param token: jwt token
    :return: current requested user
    """
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

    return user


async def authenticate_user(email: str, password: str, db: Session = Depends(get_db)):
    """
    :param email: user email address
    :param password: password
    :return: if user authenticated return user else None
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user


async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Used for creating the access token
    :param data: user data dict
    :return: jwt token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
