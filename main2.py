from fastapi import FastAPI, Header
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

@app.get('/')
async def read_root():
    return {'message': 'Hello from the main page.'}


# Path Parameter
@app.get('/greet/{name}')
async def greet(name: str) -> dict:
    return {'message': f'Hello {name}'}
# http://127.0.0.1:8000/greet/hibah


# Query Parameter
@app.get('/greet')
async def greeting(name: str) -> dict:
    return {'message': f'Hi {name}'} 
# http://127.0.0.1:8000/greet?name=hibah

# Path & Query Parameter
@app.get('/greeting/{name}')
async def greet_name_age(name: str, age: int) -> dict:
    return {'message': f'Hi {name}, Your age is {age}'}
# http://127.0.0.1:8000/greeting/hibah?age=23


# Path & Query Parameter Optional
@app.get('/greetuser')
async def greet_name_age(age: int, name:Optional[str] = 'User') -> dict:
    return {'message': f'Hi {name}, Your age is {age}'}
# http://127.0.0.1:8000/greetuser?age=30
# http://127.0.0.1:8000/greetuser?age=30&name=hibah


# Body Parameter
class BookCreateModal(BaseModel):
    title: str
    author: str

@app.post('/creat_book')
async def create_book(book_data: BookCreateModal):
    return {
        'title': book_data.title,
        'author': book_data.author
    }


# Headers Parameter
@app.get('/get_headers', status_code=200)
async def get_headers(
    accept: str = Header(None),
    content_type: str = Header(None),
    user_agent:str = Header(None),
    host: str = Header(None)
):
    request_headers = {}

    request_headers['Accept'] = accept
    request_headers['Content-Type'] = content_type,
    request_headers['User-Agent'] = user_agent,
    request_headers['Host'] = host
    

    return request_headers