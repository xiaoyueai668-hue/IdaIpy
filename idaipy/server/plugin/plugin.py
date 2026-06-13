import os
import sys
import threading

import idaapi

try:
    import rpyc
    from rpyc.utils.server import ThreadedServer
except ImportError:
    print("[IdaIpy] rpyc not installed. Run: pip install rpyc")
    rpyc = None
    ThreadedServer = None

from . import config, log, dbg

_server_instance = None
_server_thread = None

# Security: allow_pickle can be overridden with env var (not recommended)
_ALLOW_PICKLE = os.environ.get("IDAIPY_ALLOW_PICKLE", "0") == "1"

if _ALLOW_PICKLE:
    print("[IdaIpy] WARNING: IDAIPY_ALLOW_PICKLE=1 is set; "
          "pickle deserialization is enabled — this is a security risk!")


def _start_server():
    global _server_instance, _server_thread

    if _server_instance is not None:
        print("[IdaIpy] Server is already running")
        return

    from . import service as svc
    from .service import IDAService

    server = ThreadedServer(
        IDAService,
        hostname=config.HOST,
        port=config.PORT,
        protocol_config={
            "allow_all_attrs": True,
            "allow_public_attrs": True,
            "allow_pickle": _ALLOW_PICKLE,
            "allow_setattr": False,
            "allow_delattr": False,
            "sync_request_timeout": config.TIMEOUT,
        },
    )
    _server_instance = server

    def _serve():
        global _server_instance
        try:
            server.start()
        except Exception as exc:
            print(f"[IdaIpy] Server error: {exc}")
        finally:
            _server_instance = None

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    _server_thread = t

    svc._shutdown_callback = _stop_server
    log(f"RPyC server listening on {config.HOST}:{config.PORT}")


def _stop_server():
    global _server_instance, _server_thread

    if _server_instance is None:
        return
    try:
        _server_instance.close()
    except Exception:
        pass
    _server_instance = None
    _server_thread = None

    try:
        from . import service as svc
        svc._shutdown_callback = None
    except Exception:
        pass

        log("RPyC server stopped")


class IdaIpyPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_KEEP
    comment = "IdaIpy"
    help = "IdaIpy"
    wanted_name = "IdaIpy"
    wanted_hotkey = "Ctrl-Shift-R"

    def init(self):
        if rpyc is None:
            return idaapi.PLUGIN_SKIP
        log("Plugin loaded, Ctrl+Shift+R to toggle server")
        return idaapi.PLUGIN_KEEP

    def run(self, args):
        if _server_instance is not None:
            _stop_server()
        else:
            _start_server()

    def term(self):
        _stop_server()
