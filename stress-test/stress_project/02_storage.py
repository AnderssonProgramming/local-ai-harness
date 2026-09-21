"""In-memory storage layer for tasks and users."""
from typing import Dict, List, Optional
from models import Task, User

class TaskStore:
    def __init__(self):
        self._tasks: Dict[int, Task] = {}
        self._next_id = 1

    def add(self, task: Task) -> int:
        task.id = self._next_id
        self._tasks[task.id] = task
        self._next_id += 1
        return task.id

    def get(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    def delete(self, task_id: int) -> bool:
        return self._tasks.pop(task_id, None) is not None

    def list_for_user(self, owner_id: int) -> List[Task]:
        return [t for t in self._tasks.values() if t.owner_id == owner_id]

    def count_active_for_user(self, owner_id: int) -> int:
        return sum(
            1 for t in self._tasks.values()
            if t.owner_id == owner_id and t.status.value != "done"
        )

class UserStore:
    def __init__(self):
        self._users: Dict[int, User] = {}

    def add(self, user: User):
        self._users[user.id] = user

    def get(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)
