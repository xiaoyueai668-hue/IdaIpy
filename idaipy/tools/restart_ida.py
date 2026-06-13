#!/usr/bin/env python3
"""重启 IDA 9.2。"""

import os
import signal
import subprocess
import sys
import time


def restart(file_path=None):
    # 关闭
    try:
        pids = subprocess.check_output(
            ["pgrep", "-f", "MDA.app.*ida"], text=True, stderr=subprocess.DEVNULL,
        ).strip().splitlines()
        for pid in pids:
            os.kill(int(pid), signal.SIGTERM)
        print(f"已关闭: {pids}")
        time.sleep(2)
    except subprocess.CalledProcessError:
        pass

    # 启动
    cmd = ["open", "-a", "/Applications/MDA.app"]
    if file_path:
        cmd.extend(["--args", file_path])
    subprocess.Popen(cmd)
    print("IDA 已启动")


if __name__ == "__main__":
    restart(sys.argv[1] if len(sys.argv) > 1 else None)
