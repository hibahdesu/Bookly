from fastapi import FastAPI,status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from typing import List


app = FastAPI()

books = [
  {
    "id": 1,
    "title": "To Kill a Mockingbird",
    "author": "Harper Lee",
    "publisher": "J.B. Lippincott & Co.",
    "publisher_date": "1960-07-11",
    "page_count": 281,
    "language": "English"
  },
  {
    "id": 2,
    "title": "1984",
    "author": "George Orwell",
    "publisher": "Secker & Warburg",
    "publisher_date": "1949-06-08",
    "page_count": 328,
    "language": "English"
  },
  {
    "id": 3,
    "title": "One Hundred Years of Solitude",
    "author": "Gabriel García Márquez",
    "publisher": "Harper & Row",
    "publisher_date": "1970-06-05",
    "page_count": 417,
    "language": "English"
  },
  {
    "id": 4,
    "title": "The Alchemist",
    "author": "Paulo Coelho",
    "publisher": "HarperOne",
    "publisher_date": "1993-05-01",
    "page_count": 208,
    "language": "English"
  },
  {
    "id": 5,
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "publisher": "Charles Scribner's Sons",
    "publisher_date": "1925-04-10",
    "page_count": 180,
    "language": "English"
  }
]

class Book(BaseModel):
    id: int
    title: str
    author: str
    publisher: str
    publisher_date: str
    page_count: int
    language: str

class BookUpdateModel(BaseModel):
    title: str
    author: str
    publisher: str
    page_count: int
    language: str

@app.get('/books', response_model=List[Book])
async def get_all_books():
    return books
# http://127.0.0.1:8000/books

@app.post('/books', status_code=status.HTTP_201_CREATED)
async def create_a_book(book_data: Book) -> dict:
    new_book = book_data.model_dump()

    books.append(new_book)

    return new_book
# http://127.0.0.1:8000/books
"""
    { 
    "id": 7,
    "title": "Anne",
    "author": "F. Scott Fitzgerald",
    "publisher": "Charles Scribner's Sons",
    "publisher_date": "1925-04-10",
    "page_count": 180,
    "language": "English"
}
"""

@app.get('/book/{book_id}')
async def get_book(book_id: int) -> dict:
    for book in books:
        if book['id'] == book_id:
            return book
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail='Book Not Found')
# 

@app.patch('/book/{book_id}')
async def update_book(book_id: int, book_update_data: BookUpdateModel) -> dict:
    for book in books:
        if book['id'] == book_id:
            book['title'] = book_update_data.title
            book['author'] = book_update_data.author
            book['publisher'] = book_update_data.publisher
            book['page_count'] = book_update_data.page_count
            book['language'] = book_update_data.language

            return book
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Book Not Found')   

#            

@app.delete('/book/{book_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int):
    for book in books:
        if book['id'] == book_id:
            books.remove(book)

            return {}
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Book Not Found')