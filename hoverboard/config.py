max_size = 1024*1024
auto_push = True
auto_pull_global = True
auto_pull_device = True
def init(max_size=max_size,
         auto_push=auto_push,
         auto_pull_global=auto_pull_global,
         auto_pull_device=auto_pull_device):
    globs = globals()
    globs["max_size"] = max_size
    globs["auto_push"] = auto_push
    globs["auto_pull_global"] = auto_pull_global
    globs["auto_pull_device"] = auto_pull_device