from typing import List, Optional

from sqlalchemy import String, Table, Column, ForeignKey
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

association_table = Table(
    "user_task_table",
    Base.metadata,
    Column("users_id", ForeignKey("users.id"), primary_key=True),
    Column("tasks_id", ForeignKey("tasks.id"), primary_key=True),
)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    headline: Mapped[str] = mapped_column(String(256))
    text: Mapped[str]
    users: Mapped[Optional[list["User"]]] = relationship(
        secondary="user_task_table", back_populates="tasks"
    )