from clippacloud import actions
#from clippacloud.keycodes import *

max_size = 1024*1024
def init(max_size = max_size):
    globs = globals()
    globs["max_size"] = max_size