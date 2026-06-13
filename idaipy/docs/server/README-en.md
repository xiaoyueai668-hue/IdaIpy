# IdaIpy Plugin

An **RPyC**-based remote execution plugin for IDA Pro (macOS / Linux / Windows, IDA 9.0/9.1/9.2).
Execute Python scripts that call IDA API directly from external scripts, without using the IDA console.

---

## Quick Start

```bash
# 1. Install rpyc
pip3 install rpyc

# 2. Install plugin to IDA (supports macOS / Linux / Windows, auto-detects IDA version)
python3 idaipy/scripts/install_plugin.py

# 3. Open a file in IDA, press Ctrl+Shift+R to start the server

# 4. Run tests (another terminal)
python3 idaipy/scripts/test_plugin.py
```

---

## Installation

### Cross-Platform Support

The installer auto-detects your OS and IDA version:

| Platform | Detection Path |
|----------|---------------|
| macOS | `/Applications/IDA Pro {version}.app`, `/Applications/MDA.app` |
| Linux | `~/.idapro-{version}/idalinux64/plugins` |
| Windows | `C:\Program Files\IDA Pro {version}\plugins` |

### Manual Path

```bash
python3 idaipy/scripts/install_plugin.py --ida-path "/Applications/IDA Pro 9.2.app"
```

### Manual Installation

```bash
# macOS
IDA_PLUGINS="/Applications/MDA.app/Contents/MacOS/plugins"
cp server/idaipy_plugin.py "$IDA_PLUGINS/"
cp -r server/idaipy_server "$IDA_PLUGINS/"
```

---

## CLI Commands

```bash
idaipy ping                        # Health check
idaipy status                      # Server status
idaipy log --lines 50              # View log file
idaipy log --lines 50 --json      # View log as JSON
idaipy run script.py               # Execute script
idaipy run script.py -v            # Show full traceback
idaipy run script.py --timeout 300 # Custom timeout
idaipy run-project my_project       # Execute project
```

---

## Python API

### Result Type

All exec operations return a unified `Result` dataclass:

```python
from idaipy_client import IdaIpyClient, Result

with IdaIpyClient(workspace="/path/to/project") as ida:
    r = ida.run_script("script.py")
    r.raise_if_error()  # Raises on error
    print(r.stdout)
```

### Async Tasks

```python
# Async execution
task_id = ida.exec_async("import time; time.sleep(5)")
result = ida.wait_task(task_id, timeout=30)

# Batch execution
task_id = ida.exec_batch(items, chunk_size=10, yield_ms=50)
result = ida.wait_task(task_id, timeout=300)

# Cancel task
ida.cancel_task(task_id)
```

### Auto-Retry

```python
# Default: 3 retries with exponential backoff (1s, 2s, 4s)
client = IdaIpyClient(retry=3)
```

---

## Security Features

- **Token Authentication**: Enabled via `IDAIPY_TOKEN` environment variable
- **RPyC Security Hardening**: Pickle/setattr/delattr disabled by default
- **Structured Logging**: JSON to `~/.idaipy/idaipy.log`

---

## Testing

```bash
python3 idaipy/scripts/test_plugin.py    # 46 tests
python3 idaipy/scripts/test_module.py    # 15 tests
```

---

## Documentation

- [PROGRESS.md](./PROGRESS.md) — Development progress
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) — Troubleshooting
- [CLAUDE.md](../CLAUDE.md) — Claude Code context
- [design/DESIGN.md](./design/DESIGN.md) — Architecture design
