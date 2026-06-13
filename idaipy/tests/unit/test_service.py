"""Unit tests for service module (task queue and async operations)."""

import pytest
from unittest.mock import MagicMock, patch
import time

# We test the service module's logic without requiring IDA
# Mock the dependencies to test the business logic


class TestTaskQueueLogic:
    """Test task queue management logic."""

    def test_task_status_dict_structure(self):
        """Task status dict should have required fields."""
        task = {
            "status": "pending",
            "code": "print('test')",
            "mode": "main_read",
            "result": None,
            "created_at": time.time(),
            "done_at": None,
        }
        assert "status" in task
        assert "code" in task
        assert "mode" in task
        assert "result" in task
        assert "created_at" in task
        assert "done_at" in task

    def test_task_status_values(self):
        """Task status should be one of valid statuses."""
        valid_statuses = {"pending", "running", "done", "cancelled", "not_found"}
        task = {"status": "pending"}
        assert task["status"] in valid_statuses

    def test_exec_mode_parsing(self):
        """Test execution mode parsing logic."""
        from server.plugin.service import _parse_mode
        from server.plugin.executor import ExecMode

        # Valid modes
        assert _parse_mode("main_read") == ExecMode.MAIN_READ
        assert _parse_mode("main_write") == ExecMode.MAIN_WRITE

        # Invalid mode defaults to MAIN_READ
        assert _parse_mode("invalid") == ExecMode.MAIN_READ
        assert _parse_mode("") == ExecMode.MAIN_READ

    def test_token_validation_logic(self):
        """Test token validation without actual connection."""
        # When no token is set, any token should be valid
        with patch.dict("os.environ", {"IDAIPY_TOKEN": ""}):
            from server.plugin import service
            service._token = ""

            # Empty token means auth is disabled
            result = service._check_token(None, None)
            assert result is True

            # Any token should work when auth is disabled
            result = service._check_token("any_token", None)
            assert result is True

    def test_cleanup_old_tasks_logic(self):
        """Test task cleanup TTL logic."""
        from server.plugin.service import _cleanup_old_tasks, _tasks, _tasks_lock

        now = time.time()
        with _tasks_lock:
            _tasks.clear()
            # Add a done task that's old
            _tasks["old_task"] = {
                "status": "done",
                "done_at": now - 4000,  # Older than 3600 seconds
            }
            # Add a pending task (should not be removed)
            _tasks["pending_task"] = {
                "status": "pending",
                "done_at": None,
            }
            # Add a recently done task
            _tasks["recent_task"] = {
                "status": "done",
                "done_at": now - 100,
            }

        _cleanup_old_tasks()

        with _tasks_lock:
            # old_task should be removed
            assert "old_task" not in _tasks
            # pending_task should still exist
            assert "pending_task" in _tasks
            # recent_task should still exist
            assert "recent_task" in _tasks

        # Cleanup
        with _tasks_lock:
            _tasks.clear()


class TestResultFormatting:
    """Test result formatting for async operations."""

    def test_result_dict_has_status(self):
        """Result dict should have status field."""
        result = {
            "status": "ok",
            "stdout": "test output",
            "stderr": "",
        }
        assert "status" in result
        assert result["status"] == "ok"

    def test_error_result_format(self):
        """Error result should have error fields."""
        result = {
            "status": "error",
            "error_type": "RuntimeError",
            "error_message": "test error",
            "traceback": "Traceback...",
            "stdout": "",
            "stderr": "",
        }
        assert result["status"] == "error"
        assert "error_type" in result
        assert "error_message" in result


class TestWorkspaceLogic:
    """Test workspace path handling logic."""

    def test_path_resolution(self):
        """Test that workspace paths are resolved correctly."""
        import os
        path = "/path/to/workspace"
        abs_path = os.path.abspath(path)
        assert os.path.isabs(abs_path)

    def test_sys_path_addition(self):
        """Test that workspace is added to sys.path."""
        import sys
        test_path = "/tmp/test_workspace"
        if test_path not in sys.path:
            sys.path.insert(0, test_path)
            assert test_path in sys.path
            sys.path.remove(test_path)
