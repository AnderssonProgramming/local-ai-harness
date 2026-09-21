"""Notification dispatch (stubbed transport)."""
from models import Task

class NotificationChannel:
    def send(self, user_id: int, message: str):
        raise NotImplementedError

class ConsoleChannel(NotificationChannel):
    def send(self, user_id: int, message: str):
        print(f"[notify:{user_id}] {message}")

def notify_task_created(channel: NotificationChannel, task: Task):
    channel.send(task.owner_id, f"Task '{task.title}' created")

def notify_limit_reached(channel: NotificationChannel, user_id: int, limit: int):
    channel.send(user_id, f"You have reached your task limit of {limit}")

def notify_overdue(channel: NotificationChannel, task: Task):
    channel.send(task.owner_id, f"Task '{task.title}' is overdue")
