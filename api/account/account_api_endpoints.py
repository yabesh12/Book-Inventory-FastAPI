from datetime import timedelta

from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session

from api.account.utils import get_password_hash, create_access_token, get_current_user, validate_email, verify_password
from models import User
from schema import UserCreate, Token, UserLogin
from settings import get_db, ACCESS_TOKEN_EXPIRE_MINUTES

# router
router = APIRouter()

@router.post("/api/user/register", response_model=UserCreate)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    :param user: name, email, password
    :raises: if username exist
    :return: user data
    """
    validate_email(user.email)
    user_obj = db.query(User).filter(User.email == user.email).first()
    try:
        if user_obj is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="User with this email is already exist!")
        hashed_password = get_password_hash(user.password)
        new_user = User(name=user.name, email=user.email, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        raise e
    return new_user.__dict__


@router.post("/api/user/login", response_model=Token)
async def login_user(user: UserLogin, db: Session = Depends(get_db)):
    """
    :param user: email, password
    :raises: if user not registered
    :return: access token
    """
    validate_email(user.email)
    hashed_pwd = get_password_hash(user.password)
    # verify_password(user.password, hashed_pwd)
    user_obj = db.query(User).filter_by(email=user.email).first()
    if user_obj is None:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    if not user or not verify_password(user.password, user_obj.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user_obj.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/api/users", response_model=None)
async def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    :param current_user: current requested user
    :raises: if user is not admin
    :return: return all users from table User
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized! ADMIN can only access",
        )
    users = db.query(User).all()
    return users
