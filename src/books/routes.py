from fastapi import APIRouter, FastAPI,status, Depends
from fastapi.exceptions import HTTPException
from src.books.book_data import books
from src.books.schemas import Book, BookUpdateModel, BookCreateModel
from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.service import BookService
from typing import List
from src.db.main import get_session
from src.auth.dependencies import AccessTokenBearer

book_router = APIRouter()
book_service = BookService()
access_token_bearer = AccessTokenBearer()



@book_router.get('/', response_model=List[Book])
async def get_all_books(session: AsyncSession = Depends(get_session), 
                        user_details=Depends(access_token_bearer)):
    print(user_details)
    books = await book_service.get_all_books(session)
    return books
# http://127.0.0.1:8000/books

@book_router.post('/', status_code=status.HTTP_201_CREATED, response_model=Book)
async def create_a_book(book_data: BookCreateModel, session: AsyncSession = Depends(get_session), user_details=Depends(access_token_bearer)) -> dict:
    new_book = await book_service.create_book(book_data, session)

    return new_book
# http://127.0.0.1:8000/books
"""
    { 
    "title": "Anne",
    "author": "F. Scott Fitzgerald",
    "publisher": "Charles Scribner's Sons",
    "publisher_date": "1925-04-10",
    "page_count": 180,
    "language": "English"
}
"""

@book_router.get('/{book_uid}', response_model=Book)
async def get_book(book_uid: str, session: AsyncSession = Depends(get_session),
                   user_details=Depends(access_token_bearer)) -> dict:
   book = await book_service.get_book(book_uid, session)

   if book:
    return book
   else:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                        detail='Book Not Found')
# 

@book_router.patch('/{book_uid}', response_model=Book)
async def update_book(book_uid: str, book_update_data: BookUpdateModel, session: AsyncSession = Depends(get_session),
                      user_details=Depends(access_token_bearer)) -> dict:
   update_book = await book_service.update_book(book_uid, book_update_data, session)

   if update_book is None:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Book Not Found')
   else:
      return update_book
       

#            

@book_router.delete('/{book_uid}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_uid: str, session: AsyncSession = Depends(get_session),
                      user_details=Depends(access_token_bearer)):
    book_to_delete = await book_service.delete_book(book_uid, session)

    if book_to_delete is None:
       raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Book Not Found')
    else:
       return None
       