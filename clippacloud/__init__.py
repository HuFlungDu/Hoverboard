import imp
from clippacloud import config
from clippacloud import hotkey

def init(args):
    if args.config:
        userconfig = imp.load_source('userconfig', args.config)
        userconfig.init()
    else:
        config.init()
    for h in config.hotkeys:
        hotkey.bind(h[1],h[0],config.hotkeys[h])