from fastapi import HTTPException
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from auth.models import User
from task.models import Task, UserTask, TaskFile
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

    async def logout(self, request: Request) -> bool:
        """Implement logout logic here.
        This will usually clear the session with `request.session.clear()`.
        """
        request.session.clear()
        return True
        # raise NotImplementedError()


authentication_backend = AdminAuth(secret_key=SECRET)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.lastname, User.firstname, User.is_superuser, User.is_verified]


class TaskAdmin(ModelView, model=Task):
    column_list = [Task.id, Task.headline]


class UserTaskAdmin(ModelView, model=UserTask):
    column_list = [UserTask.task, UserTask.user, UserTask.completed]


class FileAdmin(ModelView, model=TaskFile):
    column_list = [TaskFile.id, TaskFile.name]
