from fastapi import FastAPI
from database import engine
from auth.usermanager import auth_backend, fastapi_users
from auth.schemas import UserCreate, UserRead
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from admin import authentication_backend, UserAdmin

from config import SECRET


app = FastAPI(
    title="OpenTask"
)
app.add_middleware(SessionMiddleware, secret_key=SECRET)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/users",
    tags=["users"]
)

admin = Admin(app, engine, authentication_backend=authentication_backend)
admin.add_view(UserAdmin)
