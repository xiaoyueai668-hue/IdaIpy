# IdaIpy Troubleshooting

> Last updated: 2026-06-13

## Table of Contents

1. [Connection Issues](#1-connection-issues)
2. [Execution Issues](#2-execution-issues)
3. [Installation Issues](#3-installation-issues)
4. [Security Issues](#4-security-issues)
5. [Logging Issues](#5-logging-issues)

---

## 1. Connection Issues

### Q: `ConnectionRefusedError: [Errno 61] Connection refused`

**Cause**: IDA server not started or port is occupied.

**Debug steps**:
1. Confirm you pressed **Ctrl+Shift+R** in IDA to start the server
2. Check IDA Output window shows `[IdaIpy] RPyC server listening on 127.0.0.1:7123`
3. Check port is not in use by another program:
   ```bash
   lsof -i :7123  # macOS/Linux
   netstat -ano | findstr :7123  # Windows
   ```

**Solution**:
- Restart IDA: make sure to open a file first, then press Ctrl+Shift+R
- Use `--port` to specify a different port: `idaipy run script.py --port 7124`

---

### Q: Connected but call timed out with `TimeoutError`

**Cause**: Code execution exceeded default timeout (600s).

**Solution**:
- Increase timeout with `--timeout`: `idaipy run script.py --timeout 1200`
- Or when creating client: `IdaIpyClient(timeout=1200)`
- Use async execution to avoid long blocking:
  ```python
  tid = ida.exec_async("import time; time.sleep(300)")
  result = ida.wait_task(tid, timeout=600)
  ```

---

### Q: Auto-reconnect failed after disconnect

**Cause**: IDA server unavailable or network issue.

**Debug steps**:
1. Confirm IDA is still running and server is started
2. Test manual connection: `idaipy ping`

**Solution**:
- Restart IDA server (Ctrl+Shift+R to stop, then Ctrl+Shift+R to start)
- Check firewall is not blocking localhost connections

---

## 2. Execution Issues

### Q: `RuntimeError: Function can be called from the main thread only`

**Cause**: IDA 9.x APIs must run on the main thread.

**Solution**:
- Use `mode="main_read"` (recommended for reads)
- Use `mode="main_write"` (for writes, requires write lock)
- No mode specified (defaults to background, but cannot call IDA API)

```python
# ✅ Correct
r = ida.run_script("script.py", mode="main_read")

# ❌ Wrong (will report main thread only)
r = ida.run_script("script.py")  # Default background mode
```

---

### Q: `Result.error: PermissionError: Invalid or missing token`

**Cause**: Server has `IDAIPY_TOKEN` env var set but client didn't pass token.

**Solution**:
- If token auth is not needed: remove `IDAIPY_TOKEN` env var on server
- If token auth is needed: client needs to support token parameter (currently CLI doesn't support token passing, upgrade client)

---

### Q: Async task `wait_task` timed out

**Cause**: Task execution exceeded specified timeout.

**Solution**:
```python
# Increase timeout
result = ida.wait_task(task_id, timeout=3600)  # 1 hour

# No timeout (wait indefinitely)
result = ida.wait_task(task_id, timeout=None)

# Check task status
status = ida.task_status(task_id)
print(status)
```

---

### Q: `ModuleNotFoundError` in remote script

**Cause**: Server can't find the module you imported.

**Solution**:
1. Use **Workspace mode** (recommended):
   ```python
   with IdaIpyClient(workspace="/path/to/your/project") as ida:
       r = ida.run_script("script.py")  # script.py can now import your project modules
   ```
2. Use **Push mode**:
   ```python
   r = ida.run_project("path/to/project", entry="main.py", use_workspace=False)
   ```
3. Use **add_path** to manually add path:
   ```python
   ida.add_path("/path/to/modules")
   ```

---

## 3. Installation Issues

### Q: `RuntimeError: IDA Pro not found`

**Cause**: Installer couldn't auto-detect IDA installation path.

**Solution**:
1. Use `--ida-path` to specify manually:
   ```bash
   # macOS
   python3 install_plugin.py --ida-path "/Applications/IDA Pro 9.2.app"

   # Linux
   python3 install_plugin.py --ida-path ~/idapro-9.2/idalinux64/plugins

   # Windows
   python3 install_plugin.py --ida-path "C:\Program Files\IDA Pro 9.2\plugins"
   ```

2. Manual install:
   ```bash
   # macOS
   IDA_PLUGINS="/Applications/MDA.app/Contents/MacOS/plugins"
   cp server/idaipy_plugin.py "$IDA_PLUGINS/"
   cp -r server/idaipy_server "$IDA_PLUGINS/"
   ```

---

### Q: `NameError: name 'IdaIpyPlugin' is not defined`

**Cause**: Python module cache (`__pycache__`) not cleaned.

**Solution**:
```bash
# Clean IDA plugins directory cache
rm -rf ~/idaipy_*/plugins/idaipy_server/__pycache__
# or
find ~/idaipy_*/plugins -name "__pycache__" -exec rm -rf {} +
```

---

### Q: `ModuleNotFoundError: No module named 'rpyc'`

**Cause**: rpyc not installed in the Python environment IDA uses.

**Solution**:
```bash
# macOS (IDA bundled Python)
/Applications/MDA.app/Contents/MacOS/python3 -m pip install rpyc

# Linux
~/idapro-9.2/idalinux64/python3 -m pip install rpyc

# or system Python (if IDA uses system Python)
pip3 install rpyc
```

---

## 4. Security Issues

### Q: `idaipy: WARNING: IDAIPY_ALLOW_PICKLE=1 is set`

**Cause**: Detected `IDAIPY_ALLOW_PICKLE=1` env var, pickle deserialization enabled.

**Risk**: `allow_pickle=True` allows deserializing arbitrary pickled objects — RCE risk.

**Solution**:
- If not needed: remove `IDAIPY_ALLOW_PICKLE` env var
- If pickle is really needed: ensure only trusted clients can connect (network isolation)

---

### Q: Token authentication failed

**Cause**: Client and server tokens don't match.

**Solution**:
1. Confirm server has `IDAIPY_TOKEN` set: `echo $IDAIPY_TOKEN`
2. Confirm client passes the correct token when connecting
3. If token auth is not needed: unset `IDAIPY_TOKEN` env var on server

---

## 5. Logging Issues

### Q: Log file doesn't exist at `~/.idaipy/idaipy.log`

**Cause**: Log directory not created or no write permission.

**Solution**:
1. Create directory manually:
   ```bash
   mkdir -p ~/.idaipy
   chmod 755 ~/.idaipy
   ```
2. Use `IDAIPY_LOG_DIR` to specify different location:
   ```bash
   IDAIPY_LOG_DIR=/tmp/idaipy_logs python3 install_plugin.py
   ```

---

### Q: How to view logs in JSON format?

**Solution**:
```bash
idaipy log --lines 100 --json
```

Or view file directly:
```bash
cat ~/.idaipy/idaipy.log | jq
```

---

### Q: Log file grows indefinitely

**Cause**: Currently no automatic log rotation.

**Temporary solution**:
```bash
# Manual rotation
mv ~/.idaipy/idaipy.log ~/.idaipy/idaipy.log.old
# Then restart IDA server (Ctrl+Shift+R)

# Or use logrotate (macOS/Linux)
# Create /etc/logrotate.d/idaipy:
# ~/.idaipy/idaipy.log {
#     rotate 5
#     size 10M
#     compress
# }
```

---

## Getting Help

1. View full logs: `idaipy log --lines 200 --json`
2. Enable client debug mode: `idaipy --debug run script.py`
3. Server debug: in IDA, edit `server/idaipy_server/config.py` set `DEBUG = True`, restart server
4. Check IDA Output window for server log output
