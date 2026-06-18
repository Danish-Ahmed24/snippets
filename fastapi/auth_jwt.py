from fastapi import APIRouter,Depends,Body,HTTPException,status
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jwt import InvalidTokenError
import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Connection
from .database import get_conn
import os
from datetime import datetime,timezone,timedelta
from typing import Annotated
from .schemas import UserCreate
from pwdlib import PasswordHash
from .sql.auth import *

SECRET_KEY=os.getenv('SECRET_KEY')
ALGORITHM=os.getenv('ALGORITHM','HS256')
ACCESS_TOKEN_EXPIRE_MINUTES=15


router = APIRouter(tags=['auth'])
auth_scheme = OAuth2PasswordBearer(tokenUrl="token")
password_hash = PasswordHash.recommended()

@router.post("/register",status_code=status.HTTP_201_CREATED)
def register(
    user_data:Annotated[UserCreate,Body()],
    conn:Annotated[Connection,Depends(get_conn)]
             ):
    username=user_data.username
    hashed_password=password_hash.hash(password=user_data.password)
    try:
        res = conn.execute(INSERT_USER,{
            "username":username,
            "hashed_password":hashed_password
        })
        
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    if res.rowcount ==0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="REGISTRATION FAILED")
    return {
            "message":"user created",
            "id":res.lastrowid
        }

@router.post("/token",include_in_schema=False)
def token(
    form_data:Annotated[OAuth2PasswordRequestForm,Depends()],
    conn:Annotated[Connection,Depends(get_conn)]
    ):
    res=verify_user(username=form_data.username,conn=conn)
    if not res:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="INCORRECT CREDENTIALS")
    
    if not password_hash.verify(password=form_data.password,hash=res['hashed_password']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="INCORRECT CREDENTIALS")
    
    payload={
        "username":res['username'],
        "exp":datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    access_token=jwt.encode(payload=payload,key=SECRET_KEY,algorithm=ALGORITHM)
    return {
        "access_token":access_token,
        "token_type":"Bearer"
    }


def get_current_user(conn:Annotated[Connection,Depends(get_conn)],token=Depends(auth_scheme)):
    try:
        payload=jwt.decode(jwt=token,key=SECRET_KEY,algorithms=[ALGORITHM])
        res=verify_user(username=payload['username'],conn=conn)
        if not res:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="jwt is altered(not possible btw)")
        return res
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="INVALID CREDENTIALS")
    
def verify_user(username:str,
                conn:Connection
                ):
    res = conn.execute(SELECT_USER_BY_USERNAME,{"username":username})
    res = res.mappings().fetchone()
    if not res:
        return None
    return res




# CREATE TABLE user(
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     username VARCHAR(255) NOT NULL UNIQUE,
#     hashed_password VARCHAR(255) NOT NULL
# );
