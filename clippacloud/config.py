from clippacloud import actions
from clippacloud.keycodes import *


hotkeys = {
    #(mod_super,k_v): actions.paste,
    #(mod_shift|mod_super,k_v): actions.paste_terminal
}
max_size = 1024
def init(hotkeys=hotkeys, max_size = max_size):
    globs = globals()
    globs["hotkeys"] = hotkeys
    globs["max_size"] = max_size