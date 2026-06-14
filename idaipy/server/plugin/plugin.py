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
    comment = "IdaIpy + MBA Editor"
    help = "IdaIpy RPyC server + MBA optimization"
    wanted_name = "IdaIpy"
    wanted_hotkey = "Ctrl-Shift-R"

    def init(self):
        if rpyc is None:
            return idaapi.PLUGIN_SKIP

        # Initialize MBA optimization functionality
        self._mba_manager = None
        self._init_mba()

        log("Plugin loaded, Ctrl+Shift+R to toggle server")
        return idaapi.PLUGIN_KEEP

    def _init_mba(self):
        """Initialize MBA optimization functionality."""
        try:
            from .ida_mba import set_manager
            from .ida_mba.mba_optimizer import MbaOptimizerManager
            self._mba_manager = MbaOptimizerManager()
            set_manager(self._mba_manager)

            # Load handlers from ~/.idaipy/handlers/
            self._load_mba_handlers()

            # Install hooks
            self._mba_manager.install()
            log("MBA optimization enabled")
        except ImportError:
            log("MBA optimization not available (HexRays?)")
        except Exception as e:
            log(f"MBA initialization failed: {e}")

    def _load_mba_handlers(self):
        """Load MBA handlers from ~/.idaipy/handlers/."""
        import os
        import importlib.util
        import sys

        handlers_dir = os.path.expanduser("~/.idaipy/handlers")
        if not os.path.exists(handlers_dir):
            return

        for filename in os.listdir(handlers_dir):
            if not filename.endswith('.py') or filename.startswith('__'):
                continue

            module_path = os.path.join(handlers_dir, filename)
            module_name = filename[:-3]

            try:
                spec = importlib.util.spec_from_file_location(
                    f"mba_handlers.{module_name}", module_path
                )
                if not spec or not spec.loader:
                    continue

                module = importlib.util.module_from_spec(spec)
                sys.modules[f"mba_handlers.{module_name}"] = module
                spec.loader.exec_module(module)

                # Register rules
                from .ida_mba.mba_optimizer import InstructionRule, BlockRule

                if hasattr(module, 'HANDLERS'):
                    for name, rule in module.HANDLERS:
                        if isinstance(rule, InstructionRule):
                            self._mba_manager.add_ins_rule(rule)
                        elif isinstance(rule, BlockRule):
                            self._mba_manager.add_blk_rule(rule)
                    log(f"Loaded {len(module.HANDLERS)} handlers from {filename}")

                elif hasattr(module, 'RULE'):
                    rule = module.RULE()
                    if isinstance(rule, InstructionRule):
                        self._mba_manager.add_ins_rule(rule)
                    elif isinstance(rule, BlockRule):
                        self._mba_manager.add_blk_rule(rule)
                    log(f"Loaded rule from {filename}")

            except Exception as e:
                log(f"Failed to load handler {filename}: {e}")

    def run(self, args):
        if _server_instance is not None:
            _stop_server()
        else:
            _start_server()

    def term(self):
        if self._mba_manager:
            self._mba_manager.remove()
        _stop_server()
