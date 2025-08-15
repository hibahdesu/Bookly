from pydantic import BaseModel, Field
from src.books.schemas import Book
from datetime import datetime
from typing import List
import uuid

class UserCreateModel(BaseModel):
    first_name: str = Field(max_length=25)
    last_name: str = Field(max_length=25)
    username: str = Field(max_length=8)
    email: str = Field(max_length=40)
    password: str = Field(min_length=8)


class UserModel(BaseModel):
    uid: uuid.UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool 
    password_hash: str 
    created_at: datetime 
    updated_at: datetime


class UserBooksModel(UserModel):
    books: List[Book]

    def __repr__(self):
        return f"<User {self.username}>"
    
class UserLoginModel(BaseModel):
    email: str = Field(max_length=40)
    password: str = Field(min_length=8)

    