from typing import List

from sqlalchemy import String, Column, ForeignKey, Boolean
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship


class UserTask(Base):
    __tablename__ = 'user_task_table'
    users_id = Column(ForeignKey('users.id'), primary_key=True)
    tasks_id = Column(ForeignKey('tasks.id'), primary_key=True)
    completed = Column(Boolean, default=False)
    task = relationship("Task", back_populates="users")
    user = relationship("User", back_populates="tasks")

    def __repr__(self):
        return f"Task {self.tasks_id} for user {self.users_id}"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    headline: Mapped[str] = mapped_column(String(256))
    text: Mapped[str]
    users: Mapped[List["UserTask"]] = relationship(back_populates="task")

    def __repr__(self):
        return self.headline
