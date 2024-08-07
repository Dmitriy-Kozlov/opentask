import datetime
from typing import List, Optional, Annotated

from sqlalchemy import String, Column, ForeignKey, Boolean, text, func, DateTime, Text
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

created_at = Annotated[datetime.datetime, mapped_column(DateTime(), server_default=func.now())]


class UserTask(Base):
    __tablename__ = 'user_task_table'
    users_id = Column(ForeignKey('users.id'), primary_key=True)
    tasks_id = Column(ForeignKey('tasks.id'), primary_key=True)
    completed = Column(Boolean, default=False)
    created_at: Mapped[created_at]
    finished_at: Mapped[datetime.datetime] = mapped_column(nullable=True)
    task = relationship("Task", back_populates="users")
    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"Task {self.tasks_id} for user {self.users_id}"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    headline: Mapped[str] = mapped_column(String(256))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[created_at]
    files: Mapped[List["TaskFile"]] = relationship(back_populates="task")
    users: Mapped[List["UserTask"]] = relationship(back_populates="task")

    def __repr__(self):
        return self.headline


class TaskFile(Base):
    __tablename__ = "taskfiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    mimetype: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[created_at]
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    task: Mapped["Task"] = relationship(back_populates="files")
    owner: Mapped["User"] = relationship(back_populates="files")

    def __repr__(self):
        return self.name