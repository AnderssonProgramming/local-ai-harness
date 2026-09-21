"""HTTP-style route handlers wiring everything together."""
from models import Task, Priority
from storage import TaskStore, UserStore
from validators import assert_valid_task_payload
from auth import require_auth
from notifications import ConsoleChannel, notify_task_created, notify_limit_reached

tasks = TaskStore()
users = UserStore()
channel = ConsoleChannel()

@require_auth
def create_task(owner_id: int, payload: dict):
    assert_valid_task_payload(payload)
    user = users.get(owner_id)
    limit = user.task_limit()
    if limit is not None and tasks.count_active_for_user(owner_id) >= limit:
        notify_limit_reached(channel, owner_id, limit)
        raise PermissionError("Task limit reached")
    task = Task(
        id=0,
        title=payload["title"],
        owner_id=owner_id,
        priority=Priority(payload.get("priority", 2)),
    )
    task_id = tasks.add(task)
    notify_task_created(channel, task)
    return task_id

@require_auth
def list_tasks(owner_id: int):
    return tasks.list_for_user(owner_id)

@require_auth
def complete_task(owner_id: int, task_id: int):
    task = tasks.get(task_id)
    if task is None or task.owner_id != owner_id:
        raise LookupError("Task not found")
    task.mark_done()
