# IdaIpy Client

Python client for remote IDA Pro API calls via RPyC.

## Three Usage Modes

### Mode 1: Standalone CLI

```bash
idaipy ping
idaipy status
idaipy run script.py
idaipy run-project my_project
```

### Mode 2: Pip Package

```bash
pip install idaipy
```

```python
from idaipy import IdaIpyClient

with IdaIpyClient() as ida:
    r = ida.run_script("script.py")
    r.raise_if_error()
    print(r.stdout)
```

### Mode 3: Development Import

```python
import sys
sys.path.insert(0, "/path/to/idaipy/client/src")
from idaipy import IdaIpyClient
```

## Installation

```bash
# From source (recommended for development)
cd idaipy/client
pip install -e .
```

## Dependencies

- Python >= 3.9
- rpyc >= 6.0
