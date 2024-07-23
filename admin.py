from fastapi import HTTPException
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from auth.models import User
from sqladmin import ModelView
from config import SECRET


class AdminAuth(AuthenticationBackend):
    async def authenticate(self, request: Request) -> bool:
        token = request.cookies.get('opentasks')
        from auth.usermanager import is_admin_token, get_jwt_strategy
        if not token or not is_admin_token(request,
                                           token,
                                           get_jwt_strategy().secret,
                                           get_jwt_strategy().token_audience,
                                           get_jwt_strategy().algorithm):
            raise HTTPException(status_code=403, detail="Not authorized to administrate")
        return True


authentication_backend = AdminAuth(secret_key=SECRET)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.is_superuser]


