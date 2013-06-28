from clippacloud import actions
from clippacloud.keycodes import *


hotkeys = {
    #(mod_super,k_v): actions.paste,
    #(mod_shift|mod_super,k_v): actions.paste_terminal
}

def init(hotkeys=hotkeys):
    globs = globals()
    globs["hotkeys"] = hotkeys