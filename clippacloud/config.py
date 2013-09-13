from clippacloud import actions

max_size = 1024*1024
auto_push = True
auto_pull = True
def init(max_size=max_size,
         auto_push=auto_push,
         auto_pull=auto_pull):
    globs = globals()
    globs["max_size"] = max_size
    globs["auto_push"] = auto_push
    globs["auto_pull"] = auto_pull