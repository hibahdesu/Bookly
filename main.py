from fastapi import FastAPI,status
from fastapi.exceptions import HTTPException
from src.books.book_data import books
from src.books.schemas import Book, BookUpdateModel
from typing import List


app = FastAPI()

