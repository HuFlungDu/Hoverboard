import imp
from clippacloud import config
from clippacloud import plugin

plugins = {}
backends = {}

def init(args,settings):
    if args.config:
        userconfig = imp.load_source('userconfig', args.config)
        userconfig.init(settings.config)
    else:
        config.init(max_size=settings.max_size,auto_push=settings.auto_push,auto_pull=settings.auto_pull)
    globals()["plugins"] = plugin.get_plugins()
    globals()["backends"] = plugins[plugin.BACKEND_PLUGIN]
    globals()["settings"] = settings