from fastapi import FastAPI
from database import engine
from auth.usermanager import auth_backend, fastapi_users
from auth.schemas import UserCreate, UserRead
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin
from admin import authentication_backend, UserAdmin, TaskAdmin, UserTaskAdmin, FileAdmin
from task.router import router as task_router
from auth.router import router as auth_router
from pages.router import router as pages_router
from config import SECRET
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="OpenTask"
)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://188.68.223.68",
    "http://188.68.223.68:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=SECRET)
app.include_router(task_router)
app.include_router(auth_router)
app.include_router(pages_router)

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
admin.add_view(TaskAdmin)
admin.add_view(UserTaskAdmin)
admin.add_view(FileAdmin)
