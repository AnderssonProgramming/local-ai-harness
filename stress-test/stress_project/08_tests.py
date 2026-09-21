"""Unit tests for the task limit business rule."""
import unittest
from models import User, MAX_TASKS_PER_USER
from storage import TaskStore
from api import create_task, users
from auth import create_session

class TestTaskLimit(unittest.TestCase):
    def setUp(self):
        self.user = User(id=1, name="Ana", email="ana@example.com")
        users.add(self.user)
        create_session(1, "tok-1")

    def test_free_user_capped_at_business_limit(self):
        for i in range(MAX_TASKS_PER_USER):
            create_task("tok-1", {"title": f"Task {i}"})
        with self.assertRaises(PermissionError):
            create_task("tok-1", {"title": "One too many"})

if __name__ == "__main__":
    unittest.main()
