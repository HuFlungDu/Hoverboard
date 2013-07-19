import imp
from clippacloud import config
from clippacloud import plugin

plugins = {}
backends = {}

def init(args):
    if args.config:
        userconfig = imp.load_source('userconfig', args.config)
        userconfig.init()
    else:
        config.init()
    globals()["plugins"] = plugin.get_plugins()
    globals()["backends"] = plugins[plugin.BACKEND_PLUGIN]
    # for h in config.hotkeys:
    #     hotkey.bind(h[1],h[0],config.hotkeys[h])