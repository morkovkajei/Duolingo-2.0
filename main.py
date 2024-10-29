import json
from datetime import date
from typing import Annotated, TypeAlias, Literal

from fastapi import FastAPI, Depends, HTTPException, Request, Response

from fastapi_users import FastAPIUsers
from fastui.forms import fastui_form
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from auth.auth import auth_backend
from auth.db import User
from auth.manager import get_user_manager
from auth.schemas import UserRead, UserCreate
from fastapi.responses import HTMLResponse
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.events import GoToEvent, BackEvent
from pydantic import BaseModel, Field, EmailStr, SecretStr
import httpx

app = FastAPI()

# auth part
fastapi_user = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)


app.include_router(
    fastapi_user.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_user.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
current_user = fastapi_user.current_user()  # use this for authed users

# auth part ended


class UserAdd(BaseModel):
    email: EmailStr = Field(title='Email')
    name: str = Field(min_length=3, max_length=25, title='Username')
    password: SecretStr = Field(title='Password', min_length=4)  # use `get_secret_value()` to decode in JSON response


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get('home', response_class=HTMLResponse)
async def read_root(request: Request, user: User = Depends(current_user)):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post('/api/log', response_model=FastUI, response_model_exclude_none=True)
async def login_user(form: Annotated[UserAdd, fastui_form(UserAdd)], response: Response):
    try:
        async with httpx.AsyncClient() as client:
            log_response = await client.post(
                'http://127.0.0.1:8000/auth/jwt/login',
                data={
                    "grant_type": "password",
                    "username": form.email,  # тут вместо form.username -> form.email (так и должно быть!)
                    "password": form.password.get_secret_value(),
                    "scope": "",
                    "client_id": "",
                    "client_secret": ""
                }
            )
            jwt_token = str(log_response.headers.get("set-cookie"))
            header = jwt_token.split('.')[0].split('=')[1]
            payload = jwt_token.split('.')[1]
            verify_signature = jwt_token.split('.')[2].split(';')[0]
            print(header)
            print(payload)
            print(verify_signature)
            jwt_token = f'{header}.{payload}.{verify_signature}'
            response.set_cookie(key='bonds',
                                value=jwt_token,
                                secure=True,
                                httponly=True,
                                samesite="Lax")
        return [
            c.Page(
                components=[
                    c.Paragraph(text='You successfully login'),
                    c.Button(text='To home', on_click=GoToEvent(url='/home'))
                ]
            )
        ]
    except Exception as e:
        return [
            c.Page(
                components=[
                    c.Paragraph(text='Something went bad...'),
                    c.Button(text='To Main', on_click=GoToEvent(url='/'))
                ]
            )
        ]


@app.post('/api/sign', response_model=FastUI, response_model_exclude_none=True)
async def add_user(form: Annotated[UserAdd, fastui_form(UserAdd)]):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'http://127.0.0.1:8000/auth/register',
                json={
                    'email': form.email,
                    'username': form.name,
                    'password': form.password.get_secret_value(),
                }
            )
            return [
                c.Page(
                    components=[
                        c.Paragraph(text='You successfully Sing Up'),
                        c.Button(text="Let's login", on_click=GoToEvent(url='/login'))
                    ]
                )
            ]
    except Exception as e:
        return [
            c.Page(
                components=[
                    c.Paragraph(text='Something went bad...'),
                    c.Button(text='To Main', on_click=GoToEvent(url='/'))
                ]
            )
        ]


@app.get('/api/logout', response_model=FastUI, response_model_exclude_none=True)
async def logout_user(response: Response):
    response.delete_cookie(key="bonds")
    return [
        c.Page(
            components=[
                c.Paragraph(text='You successfully logout'),
                c.Button(text='To Main', on_click=GoToEvent(url='/'))
            ]
        )
    ]


@app.get('/api/login', response_model=FastUI, response_model_exclude_none=True)
def login_page():
    return [
        c.Page(
            components=[
                c.Button(text='To main menu', on_click=GoToEvent(url='/')),
                c.Heading(text='Login', level=2),
                c.ModelForm(
                    model=UserAdd,
                    submit_url='api/log'
                ),
            ]
        )
    ]


@app.get('/api/sign_up', response_model=FastUI, response_model_exclude_none=True)
def signup_page():
    return [
        c.Page(
            components=[
                c.Button(text='To main menu', on_click=GoToEvent(url='/')),
                c.Heading(text='Sign Up', level=2),
                c.ModelForm(
                    model=UserAdd,
                    submit_url='api/sign'
                ),
            ]
        )

    ]


@app.get('/api/', response_model=FastUI, response_model_exclude_none=True)
def default_page() -> list[AnyComponent]:
    return [
        c.Page(
            components=[
                c.Button(text='Sign Up', on_click=GoToEvent(url='sign_up')),
                c.Button(text='Login', on_click=GoToEvent(url='login')),
                c.Button(text='LogOut', on_click=GoToEvent(url='logout'))
            ]
        ),
    ]


@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:

    return HTMLResponse(prebuilt_html(title='FastUI'))

