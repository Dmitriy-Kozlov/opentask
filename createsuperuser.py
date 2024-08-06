import contextlib

from fastapi_users.exceptions import UserAlreadyExists

from auth.models import get_user_db
from auth.schemas import UserCreate
from auth.usermanager import get_user_manager
from database import get_async_session

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(email: str, password: str, username: str, lastname: str, firstname: str, is_superuser: bool = False):
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.create(
                        UserCreate(
                            email=email, username=username,
                            lastname=lastname, firstname=firstname,
                            password=password, is_superuser=is_superuser,
                            tasks=[], files=[]
                        )
                    )
                    print(f"User created {user}")
                    return user
    except UserAlreadyExists:
        print(f"User {email} already exists")
        raise

import asyncio

if __name__ == "__main__":
  asyncio.run(create_user(email="admin@admin.com", username="admin", lastname="admin", firstname="admin", password="admin", is_superuser=True))