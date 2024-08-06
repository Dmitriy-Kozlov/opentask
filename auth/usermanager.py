from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin, exceptions, models, schemas
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
import jwt
from sqlalchemy import select

from config import SECRET

from fastapi_users.db import SQLAlchemyUserDatabase

from database import async_session_maker
from .models import User, get_user_db
from fastapi_users.jwt import generate_jwt, decode_jwt


def is_admin_token(request, token, decode_key, token_audience, algorithms):
    try:
        data = decode_jwt(
            token, decode_key, token_audience, algorithms
        )
        is_admin = data.get("admin")
    except jwt.PyJWTError:
        return None
    return is_admin


class MyJWTStrategy(JWTStrategy):
    async def write_token(self, user: models.UP) -> str:
        data = {"sub": str(user.id), "aud": self.token_audience, "admin": user.is_superuser}
        return generate_jwt(
            data, self.encode_key, self.lifetime_seconds, algorithm=self.algorithm
        )


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def create(
        self,
        user_create: schemas.UC,
        safe: bool = False,
        request: Optional[Request] = None,
    ) -> models.UP:
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise exceptions.UserAlreadyExists()

        user_dict = (
            user_create.create_update_dict()
            if safe
            else user_create.create_update_dict_superuser()
        )
        password = user_dict.pop("password")
        user_dict["hashed_password"] = self.password_helper.hash(password)
        created_user = await self.user_db.create(user_dict)

        await self.on_after_register(created_user, request)

        return created_user


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(cookie_name="opentasks", cookie_max_age=86400)


def get_jwt_strategy() -> MyJWTStrategy:
    return MyJWTStrategy(secret=SECRET, lifetime_seconds=86400)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True, verified=True)


async def get_all_users():
    async with async_session_maker() as session:
        query = select(User)
        result = await session.execute(query)
        users = result.scalars().all()
        return users
