#!/usr/bin/env python3
"""安装 IdaIpy 插件到 IDA Pro plugins 目录，然后重启 IDA。

支持 macOS, Linux, Windows。自动检测 IDA 版本（9.0/9.1/9.2）。
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import signal
import subprocess
import sys
import time


IDA_VERSIONS = ["9.2", "9.1", "9.0"]


def _detect_ida_path() -> str:
    """Detect IDA Pro installation path based on OS and version.

    Raises:
        RuntimeError: If IDA Pro cannot be found.
    """
    system = platform.system()
    home = os.path.expanduser("~")

    if system == "Darwin":
        # macOS: IDA Pro is distributed as .app bundles
        for version in IDA_VERSIONS:
            # IDA Pro 9.x on macOS is typically named "IDA Pro <version>.app"
            # or just "IDA.app" / "MDA.app" for Hex-Rays builds
            app_name = f"IDA Pro {version}.app"
            path = f"/Applications/{app_name}"
            if os.path.isdir(path):
                return path
            # Also check for Hex-Rays branded versions
            mda_path = "/Applications/MDA.app"
            if os.path.isdir(mda_path):
                return mda_path
        # Try default MDA.app location
        default = "/Applications/MDA.app"
        if os.path.isdir(default):
            return default
        raise RuntimeError(
            f"IDA Pro not found on macOS. Checked /Applications for:\n" +
            "\n".join(f"  - IDA Pro {v}.app" for v in IDA_VERSIONS) +
            f"\n  - MDA.app\n\n"
            "Download IDA Pro from https://www.hex-rays.com/"
        )

    elif system.startswith("Linux"):
        for version in IDA_VERSIONS:
            ida_home = os.path.join(home, f"idapro-{version}")
            plugin_path = os.path.join(ida_home, "idalinux64", "plugins")
            if os.path.isdir(plugin_path):
                return plugin_path
        # Check common alternatives
        for version in IDA_VERSIONS:
            for suffix in ("", "-pro"):
                alt = os.path.join(
                    home, f"ida{suffix}-{version}", "idalinux64", "plugins"
                )
                if os.path.isdir(alt):
                    return alt
        raise RuntimeError(
            f"IDA Pro not found on Linux. Checked:\n" +
            "\n".join(f"  - {home}/idapro-{v}/idalinux64/plugins" for v in IDA_VERSIONS) +
            "\n\nDownload IDA Pro from https://www.hex-rays.com/ and extract to ~/idapro-<version>/"
        )

    elif system == "Windows":
        program_files = os.environ.get(
            "ProgramFiles",
            "C:\\Program Files"
        )
        program_files_x86 = os.environ.get(
            "ProgramFiles(x86)",
            "C:\\Program Files (x86)"
        )
        for version in IDA_VERSIONS:
            for pf in (program_files, program_files_x86):
                path = os.path.join(pf, f"IDA Pro {version}", "plugins")
                if os.path.isdir(path):
                    return path
        raise RuntimeError(
            f"IDA Pro not found on Windows. Checked:\n" +
            "\n".join(
                f"  - {pf}\\IDA Pro {v}\\plugins"
                for v in IDA_VERSIONS
                for pf in (program_files, program_files_x86)
            ) +
            "\n\nDownload IDA Pro from https://www.hex-rays.com/"
        )

    else:
        raise RuntimeError(
            f"Unsupported platform: {system}. "
            "IdaIpy supports macOS, Linux, and Windows."
        )


def _get_plugins_dir(ida_path: str) -> str:
    """Get the plugins directory for the IDA installation."""
    system = platform.system()
    if system == "Darwin":
        return os.path.join(ida_path, "Contents", "MacOS", "plugins")
    elif system.startswith("Linux"):
        return os.path.join(ida_path, "idalinux64", "plugins")
    elif system == "Windows":
        return os.path.join(ida_path, "plugins")
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def _kill_ida(ida_path: str) -> None:
    """Kill running IDA processes."""
    system = platform.system()
    try:
        if system == "Darwin":
            # Find by app name
            pids = subprocess.check_output(
                ["pgrep", "-f", "IDA Pro|MDA.app|ida"],
                text=True, stderr=subprocess.DEVNULL,
            ).strip().splitlines()
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
        elif system.startswith("Linux"):
            pids = subprocess.check_output(
                ["pgrep", "-f", "idalinux64|ida"],
                text=True, stderr=subprocess.DEVNULL,
            ).strip().splitlines()
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
        elif system == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/IM", "ida.exe"],
                capture_output=True, text=True,
            )
    except subprocess.CalledProcessError:
        pass  # No IDA process running
    time.sleep(2)


def _start_ida(ida_path: str) -> None:
    """Start IDA."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", "-a", ida_path])
        elif system.startswith("Linux"):
            ida_bin = os.path.join(ida_path, "idalinux64", "ida")
            if os.path.exists(ida_bin):
                subprocess.Popen([ida_bin])
            else:
                subprocess.Popen([ida_path])  # fallback
        elif system == "Windows":
            ida_exe = os.path.join(ida_path, "ida.exe")
            if os.path.exists(ida_exe):
                subprocess.Popen([ida_exe])
            else:
                subprocess.Popen([ida_path])
    except Exception as exc:
        print(f"Warning: Could not start IDA: {exc}")


def install(ida_path: str, restart: bool = True) -> None:
    """Install idaipy plugin to IDA's plugins directory."""
    plugins_dir = _get_plugins_dir(ida_path)
    os.makedirs(plugins_dir, exist_ok=True)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    server_dir = os.path.join(project_root, "server")
    plugin_loader = os.path.join(server_dir, "idaipy_plugin.py")
    server_pkg = os.path.join(server_dir, "plugin")

    # 1. Copy loader
    dst_loader = os.path.join(plugins_dir, "idaipy_plugin.py")
    shutil.copy2(plugin_loader, dst_loader)
    print(f"已复制: {dst_loader}")

    # 2. Copy idaipy_server package
    dst_pkg = os.path.join(plugins_dir, "idaipy_server")
    if os.path.exists(dst_pkg):
        shutil.rmtree(dst_pkg)
    shutil.copytree(
        server_pkg, dst_pkg,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    print(f"已复制: {dst_pkg}")

    # 3. Ensure rpyc is available
    try:
        import rpyc  # noqa: F401
        print(f"rpyc OK: {rpyc.__file__}")
    except ImportError:
        print("安装 rpyc...")
        subprocess.run([sys.executable, "-m", "pip", "install", "rpyc"])

    print(f"\nIdaIpy 插件已安装到: {plugins_dir}")
    print("在 IDA 中按 Ctrl+Shift+R 启动/停止服务")


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="安装 IdaIpy 插件到 IDA Pro",
    )
    parser.add_argument(
        "--ida-path",
        default=None,
        help="IDA 安装路径（自动检测如果不指定）",
    )
    parser.add_argument(
        "--no-restart",
        action="store_true",
        help="不自动重启 IDA",
    )
    args = parser.parse_args(argv)

    # Detect or use provided IDA path
    if args.ida_path:
        if not os.path.isdir(args.ida_path):
            print(f"错误: IDA 路径不存在: {args.ida_path}", file=sys.stderr)
            return 1
        ida_path = args.ida_path
    else:
        try:
            ida_path = _detect_ida_path()
            print(f"检测到 IDA: {ida_path}")
        except RuntimeError as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1

    restart = not args.no_restart
    if restart:
        print("关闭 IDA...")
        _kill_ida(ida_path)

    print("安装插件...")
    install(ida_path, restart=restart)

    if restart:
        time.sleep(1)
        print("启动 IDA...")
        _start_ida(ida_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
