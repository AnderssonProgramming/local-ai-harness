"""Domain models for the TaskFlow application."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# BUSINESS RULE: no free-tier account may exceed this many active tasks.
MAX_TASKS_PER_USER = 47

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"

@dataclass
class Task:
    id: int
    title: str
    owner_id: int
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    created_at: datetime = field(default_factory=datetime.utcnow)
    tags: list = field(default_factory=list)

    def mark_done(self):
        self.status = TaskStatus.DONE

    def is_overdue(self, due_date: datetime) -> bool:
        return datetime.utcnow() > due_date and self.status != TaskStatus.DONE

@dataclass
class User:
    id: int
    name: str
    email: str
    is_premium: bool = False

    def task_limit(self) -> int:
        return None if self.is_premium else MAX_TASKS_PER_USER
