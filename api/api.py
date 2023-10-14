from collections import OrderedDict
from typing import List
from hash import *
from jwt import *

import contextlib
import logging.config
import sqlite3
import datetime

from fastapi import FastAPI, Depends, Request, HTTPException, status
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class UserRegister(BaseModel):
    username: str
    password: str
    roles: List[str]

class UserSignIn(BaseModel):
    username: str
    password: str

class Settings(BaseSettings, env_file=".env", extra="ignore"):
    database: str
    logging_config: str

def get_db():
    with contextlib.closing(sqlite3.connect(settings.database)) as db:
        db.row_factory = sqlite3.Row
        yield db

def get_logger():
    return logging.getLogger(__name__)

settings = Settings()
app = FastAPI()

logging.config.fileConfig(settings.logging_config, disable_existing_loggers=False)


# Task 1: Register a new user
# Example: POST http://localhost:5000/register
# body: {
#     "username": "TheRealSamDoe",
#     "password": "SamyDoeSo123!",
#     "roles": ["student"]
# }
@app.post("/register")
def register(new_register: UserRegister, request: Request, db: sqlite3.Connection = Depends(get_db)):

    new_user = dict(new_register)
    
    username_exists = db.execute("""
                SELECT *
                FROM User
                WHERE username=:username
            """, new_user).fetchall()
    
    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already in use."
        )
    
    hashed_password = hash_password(new_user["password"])

    db.execute("""
        INSERT INTO User (username, password)
        VALUES (:username, :hashed_password)
        """, {"username": new_user["username"], "hashed_password": hashed_password})
    
    for role in new_user["roles"]:
            db.execute("""
                INSERT INTO Roles (r_username, role)
                VALUES (:username, :role)
        """, {"username": new_user["username"], "role": role})

    claims = generate_claims(new_user["username"], new_user["roles"])
    
    # Commit the changes
    db.commit()
    
    return claims

# Task 1: Register a new user
# Example: POST http://localhost:5000/signin
# body: {
#     "username": "TheRealSamDoe",
#     "password": "SamyDoeSo123!",
# }
@app.post("/signin")
def signin(user_sign_in: UserSignIn, request: Request, db: sqlite3.Connection = Depends(get_db)):
    
    user = dict(user_sign_in)

    user_info = db.execute("""
            SELECT *
            FROM User
            WHERE username=:username
        """, user).fetchall()[0]
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials."
        ) 
    
    verified = verify_password(user["password"], user_info["password"])

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials."
        )   

    user_roles = db.execute("""
                SELECT *
                FROM Roles
                WHERE r_username=:username
            """, user).fetchall()
    
    roles = []
    for role in user_roles:
        roles.append(role["role"])

    claims = generate_claims(user_info["username"], roles)
    
    return claims