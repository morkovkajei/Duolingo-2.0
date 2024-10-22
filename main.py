from fastapi import FastAPI, HTTPException
from typing import Optional, List, Dict
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    age: int

class Post(BaseModel):
    id: int
    title: str
    body: str
    author: User

class PostCreate(BaseModel):
    title: str
    body: str
    author_id: int

users = [
    {'id':1, 'name':'John','age':34},
    {'id':2, 'name':'Max','age':25},
    {'id':3, 'name':'Mark','age':17}
]

posts = [
    {'id':1, 'title':'News 1', 'body':'Text 1', 'author': users[1]},
    {'id':2, 'title':'News 2', 'body':'Text 2', 'author': users[0]},
    {'id':3, 'title':'News 3', 'body':'Text 3', 'author': users[2]}
]

@app.get('/items')
async def items() -> List[Post]:
    return [Post(**post) for post in posts]