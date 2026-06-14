"""idaipy CLI — 执行本地脚本或项目。

用法:
    idaipy run example/gather_info.py
    idaipy run-project example/my_project --entry run.py
    idaipy ping
    idaipy status
    idaipy log --lines 50
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from typing import List, Optional

from . import __version__
from .client import IdaIpyClient
from .result import Result


# Default log file location
DEFAULT_LOG_DIR = os.path.expanduser("~/.idaipy")
DEFAULT_LOG_FILE = os.path.join(DEFAULT_LOG_DIR, "idaipy.log")


def _err(msg: str) -> None:
    """Print error to stderr with consistent format."""
    print(f"idaipy: error: {msg}", file=sys.stderr)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="idaipy",
        description="IdaIpy — 执行本地 Python 脚本到远程 IDA",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=7123)
    parser.add_argument("--workspace", default=None,
                        help="服务端 workspace 路径")
    parser.add_argument("--debug", action="store_true")

    sub = parser.add_subparsers(dest="command")

    # run command
    p_run = sub.add_parser("run", help="执行本地 .py 文件")
    p_run.add_argument("script", help="脚本路径")
    p_run.add_argument("--mode", default="main_read",
                       choices=("main_read", "main_write"))
    p_run.add_argument("--json", dest="as_json", action="store_true",
                       help="解析 stdout 最后一行为 JSON")
    p_run.add_argument("--verbose", "-v", action="store_true",
                        help="显示完整 traceback")
    p_run.add_argument("--timeout", type=int, default=None,
                        help="超时时间（秒）")

    # run-project command
    p_proj = sub.add_parser("run-project", help="执行项目目录")
    p_proj.add_argument("project_dir", help="项目根目录")
    p_proj.add_argument("--entry", default="main.py", help="入口脚本")
    p_proj.add_argument("--mode", default="main_read",
                        choices=("main_read", "main_write"))
    p_proj.add_argument("--push", action="store_true",
                        help="push 模式（而非 workspace）")
    p_proj.add_argument("--verbose", "-v", action="store_true",
                        help="显示完整 traceback")
    p_proj.add_argument("--timeout", type=int, default=None,
                        help="超时时间（秒）")

    # ping command
    sub.add_parser("ping", help="健康检查")

    # status command
    sub.add_parser("status", help="服务状态")

    # log command
    p_log = sub.add_parser("log", help="查看本地日志文件")
    p_log.add_argument("--lines", "-n", type=int, default=50,
                       help="显示最后 N 行（默认 50）")
    p_log.add_argument("--json", action="store_true",
                       help="以 JSON 格式输出")

    # mba command
    p_mba = sub.add_parser("mba", help="MBA (Microcode) 优化命令")
    p_mba.add_argument("action", nargs="?",
                       choices=("list", "reload", "status"),
                       help="操作：list=列出所有, reload=热更新, status=查看状态")
    p_mba.add_argument("handler_name", nargs="?", help="handler 名称")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    try:
        return _dispatch(args)
    except ConnectionRefusedError:
        host = args.host or os.environ.get("IDAIPY_HOST", "127.0.0.1")
        port = args.port or int(os.environ.get("IDAIPY_PORT", "7123"))
        _err(f"无法连接 {host}:{port}")
        return 1
    except Exception as exc:
        _err(str(exc))
        return 1


def _dispatch(args: argparse.Namespace) -> int:
    if args.command in ("ping", "status"):
        # These commands don't need a full client connection,
        # just a quick check via rpyc
        import rpyc
        host = args.host or os.environ.get("IDAIPY_HOST", "127.0.0.1")
        port = args.port or int(os.environ.get("IDAIPY_PORT", "7123"))
        try:
            conn = rpyc.connect(
                host, port,
                config={"sync_request_timeout": 5}
            )
            try:
                if args.command == "ping":
                    pong = conn.root.ping()
                    print(f"idaipy: pong: {pong}")
                    return 0
                else:  # status
                    status = conn.root.get_status()
                    print(f"idaipy: status: {json.dumps(status, indent=2)}")
                    return 0
            finally:
                conn.close()
        except Exception as exc:
            _err(f"无法连接 {host}:{port}: {exc}")
            return 1

    elif args.command == "log":
        log_file = os.environ.get(
            "IDAIPY_LOG_FILE",
            os.path.join(
                os.environ.get("IDAIPY_LOG_DIR", DEFAULT_LOG_DIR),
                "idaipy.log"
            )
        )
        if not os.path.exists(log_file):
            _err(f"日志文件不存在: {log_file}")
            return 1
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        tail = lines[-args.lines:] if args.lines > 0 else lines
        if args.json:
            for line in tail:
                line = line.strip()
                if line:
                    try:
                        obj = json.loads(line)
                        print(json.dumps(obj, ensure_ascii=False))
                    except json.JSONDecodeError:
                        print(line)
        else:
            print("".join(tail), end="")
        return 0

    elif args.command in ("run", "run-project"):
        # Build client
        client_kwargs = {
            "host": args.host,
            "port": args.port,
            "workspace": args.workspace,
            "debug": args.debug,
        }
        if hasattr(args, "timeout") and args.timeout is not None:
            client_kwargs["timeout"] = args.timeout

        client = IdaIpyClient(**client_kwargs)
        with client:
            return _dispatch_script(client, args)

    elif args.command == "mba":
        client_kwargs = {
            "host": args.host,
            "port": args.port,
            "debug": args.debug,
        }
        client = IdaIpyClient(**client_kwargs)
        with client:
            return _dispatch_mba(client, args)
    return 0


def _dispatch_mba(client: IdaIpyClient, args: argparse.Namespace) -> int:
    """处理 MBA 子命令。"""
    action = args.action

    if action is None:
        # 没有指定 action，打印帮助
        print("idaipy mba - MBA (Microcode) 优化命令")
        print("")
        print("用法:")
        print("  idaipy mba list              # 列出所有 handlers")
        print("  idaipy mba reload <name>     # 热更新指定 handler")
        print("  idaipy mba status <name>     # 查看 handler 状态")
        return 0

    if action == "list":
        handlers = client.list_mba_handlers()
        if not handlers:
            print("没有已注册的 handlers")
            return 0
        print(f"{'Name':<20} {'Status':<12} {'Rules':<8} {'In SysModules'}")
        print("-" * 60)
        for h in handlers:
            print(f"{h.get('name', ''):<20} {h.get('status', ''):<12} "
                  f"{h.get('rule_count', 0):<8} {h.get('in_sys_modules', False)}")
        return 0

    elif action == "reload":
        if not args.handler_name:
            _err("reload 需要指定 handler 名称")
            return 1
        result = client.reload_mba_handler(args.handler_name)
        if result.ok:
            print(f"Handler '{args.handler_name}' 热更新成功，"
                  f"规则数: {result.stdout}")
        else:
            print(f"Error: {result.error_message}", file=sys.stderr)
            return 1
        return 0

    elif action == "status":
        if not args.handler_name:
            _err("status 需要指定 handler 名称")
            return 1
        status = client.get_mba_handler_status(args.handler_name)
        print(f"Handler: {status.get('name')}")
        print(f"Status: {status.get('status')}")
        print(f"Rules: {status.get('rule_count', 0)}")
        print(f"In SysModules: {status.get('in_sys_modules', False)}")
        return 0

    return 0


def _dispatch_script(client: IdaIpyClient, args: argparse.Namespace) -> int:
    show_traceback = getattr(args, "verbose", False)

    if args.command == "run":
        if getattr(args, "as_json", False):
            data = client.run_script_json(args.script, mode=args.mode)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            r = client.run_script(args.script, mode=args.mode)
            if r.ok:
                if r.stdout:
                    print(r.stdout, end="")
            else:
                print(f"idaipy: ERROR [{r.error_type}]: {r.error_message}",
                      file=sys.stderr)
                if show_traceback and r.traceback:
                    print(r.traceback, file=sys.stderr)
                return 1

    elif args.command == "run-project":
        r = client.run_project(
            args.project_dir, entry=args.entry,
            mode=args.mode,
            use_workspace=not getattr(args, "push", False),
        )
        if r.ok:
            if r.stdout:
                print(r.stdout, end="")
        else:
            print(f"idaipy: ERROR [{r.error_type}]: {r.error_message}",
                  file=sys.stderr)
            if show_traceback and r.traceback:
                print(r.traceback, file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
