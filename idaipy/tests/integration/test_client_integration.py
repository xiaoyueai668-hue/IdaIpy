"""集成测试：使用 idaipy 包测试客户端功能.

要求：IDA 运行中且服务已启动（Ctrl+Shift+R）
"""

import os
import sys
import tempfile

import pytest


class TestConnection:
    """测试连接管理功能."""

    def test_basic_connection(self):
        """基本连接测试：使用默认地址连接."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            assert c.is_connected()
            # 通过执行简单脚本验证连接
            r = c._exec_code("print('connected')", mode="main_read")
            assert r.ok
            assert "connected" in r.stdout

    def test_custom_connection(self):
        """自定义地址连接测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient(host="127.0.0.1", port=7123) as c:
            assert c.is_connected()
            r = c._exec_code("print('connected')", mode="main_read")
            assert r.ok

    def test_connection_check_methods(self):
        """连接检查方法测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            # is_connected
            assert c.is_connected()

            # 通过执行简单代码验证连接可用
            r = c._exec_code("1 + 1", mode="main_read")
            assert r.ok


class TestScriptExecution:
    """测试脚本执行功能."""

    def test_execute_simple_script(self):
        """执行简单脚本测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c.run_script("/dev/stdin", mode="main_read")
            # 注意：直接执行代码
            r = c._exec_code("print('hello from idaipy')", mode="main_read")
            assert r.ok
            assert "hello from idaipy" in r.stdout

    def test_execute_main_read_mode(self):
        """main_read 模式执行测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c._exec_code("import idaapi; print(idaapi.get_kernel_version())", mode="main_read")
            assert r.ok
            assert len(r.stdout) > 0

    def test_execute_main_write_mode(self):
        """main_write 模式执行测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c._exec_code("x = 1 + 2; print(x)", mode="main_write")
            assert r.ok
            assert "3" in r.stdout

    def test_run_script_file_not_found(self):
        """脚本文件不存在测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            with pytest.raises(FileNotFoundError):
                c.run_script("/nonexistent/script.py")

    def test_error_handling(self):
        """错误处理测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c._exec_code("raise ValueError('test error')", mode="main_read")
            assert not r.ok
            assert r.status == "error"
            assert r.error_type == "ValueError"
            assert "test error" in r.error_message


class TestAsyncTasks:
    """测试异步任务功能."""

    def test_exec_async_returns_task_id(self):
        """异步任务提交测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            task_id = c.exec_async("print('async task')", mode="main_read")
            assert isinstance(task_id, str)
            assert len(task_id) > 0

    def test_wait_task_completes(self):
        """等待任务完成测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            task_id = c.exec_async("import time; time.sleep(0.5); print('done')", mode="main_read")
            result = c.wait_task(task_id, timeout=10)
            assert result["state"] == "done"
            assert result["result"]["status"] == "ok"
            assert "done" in result["result"].get("stdout", "")

    def test_task_status(self):
        """任务状态查询测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            task_id = c.exec_async("print('quick')", mode="main_read")
            status = c.task_status(task_id)
            assert "status" in status
            assert status["status"] in ("pending", "running", "done")

    def test_list_tasks(self):
        """列出所有任务测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            task_id = c.exec_async("print('task1')", mode="main_read")
            tasks = c.list_tasks()
            assert isinstance(tasks, list)
            # 刚提交的任务应该在列表中
            task_ids = [t.get("task_id") for t in tasks]
            assert task_id in task_ids


class TestWorkspace:
    """测试 Workspace 功能."""

    def test_set_workspace(self):
        """设置 workspace 测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            # 使用临时目录
            with tempfile.TemporaryDirectory() as tmpdir:
                msg = c.set_workspace(tmpdir)
                assert "Workspace set to" in msg or tmpdir in msg

    def test_get_workspace(self):
        """获取 workspace 测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            with tempfile.TemporaryDirectory() as tmpdir:
                c.set_workspace(tmpdir)
                ws = c.get_workspace()
                assert tmpdir in ws or ws == tmpdir

    def test_workspace_injected_to_execution(self):
        """Workspace 注入到执行环境测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            with tempfile.TemporaryDirectory() as tmpdir:
                c.set_workspace(tmpdir)
                r = c._exec_code("print(WORKSPACE)", mode="main_read")
                assert r.ok


class TestBatchExecution:
    """测试批量执行功能."""

    def test_exec_batch(self):
        """批量执行测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            items = ["item1", "item2", "item3"]
            task_id = c.exec_batch(items, chunk_size=2, yield_ms=50)
            assert isinstance(task_id, str)

            result = c.wait_task(task_id, timeout=30)
            assert result["state"] == "done"


class TestResult:
    """测试 Result 对象."""

    def test_result_ok(self):
        """正常结果测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c._exec_code("print('success')", mode="main_read")
            assert r.ok
            assert r.status == "ok"
            assert "success" in r.stdout

    def test_result_error(self):
        """错误结果测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c._exec_code("raise RuntimeError('test error')", mode="main_read")
            assert not r.ok
            assert r.status == "error"
            assert r.error_type == "RuntimeError"

    def test_raise_if_error(self):
        """raise_if_error 方法测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c._exec_code("print('ok')", mode="main_read")
            # 不应抛出异常
            r.raise_if_error()

    def test_raise_if_error_raises(self):
        """raise_if_error 在错误时抛出异常测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c._exec_code("raise ValueError('error')", mode="main_read")
            with pytest.raises(RuntimeError) as exc_info:
                r.raise_if_error()
            assert "ValueError" in str(exc_info.value)

    def test_result_get_method(self):
        """get 方法测试."""
        from idaipy import IdaIpyClient

        with IdaIpyClient() as c:
            r = c._exec_code("print('test')", mode="main_read")
            assert r.get("status") == "ok"
            assert r.get("stdout") == r.stdout
            assert r.get("nonexistent", "default") == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
