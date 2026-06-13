"""IdaIpy plugin entry point — IDA loads this file.

当 IDA 加载此插件时，它会调用 PLUGIN_ENTRY() 创建插件实例。
"""

import idaipy_server.plugin as plugin

def PLUGIN_ENTRY():
    return plugin.IdaIpyPlugin()
