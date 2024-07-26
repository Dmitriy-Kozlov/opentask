from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_async_session
from .models import User
from .schemas import UserRead
from .usermanager import current_active_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/all", response_model=list[UserRead])
async def get_all_users(session: AsyncSession = Depends(get_async_session),
                        user: User = Depends(current_active_user),):
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized get all users list")
    query = select(User)
    result = await session.execute(query)
    users = result.unique().scalars().all()
    return users
