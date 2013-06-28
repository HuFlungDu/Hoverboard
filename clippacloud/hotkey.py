import threading
from clippacloud import exceptions
from clippacloud import keycodes


__backend = None

try:
    import win32api
    __backend = "win32"
except ImportError:
    try:
        import keybinder
        import gtk
        __backend = "Xorg"
    except:
        __backend = "Mac"
        #raise exceptions.BackendNotFoundError("Backend not found for binding keys")

if __backend == "Xorg":
    def bind(key,mask,callback,*userdata):
        bindstring = gtk.accelerator_name(key,mask)
        if len(userdata):
            keybinder.bind(bindstring,callback,userdata)
        else:
            keybinder.bind(bindstring,callback)
    mod_keys_pressed = []            
    def mod_key_pressed(keycode):
        mod_keys_pressed.append(keycode)
    

        
elif __backend == "win32":
    def bind(key,mask,callback,*userdata):
        pass
    pass

elif __backend == "Mac":
    def bind(key,mask,callback,*userdata):
        pass
    pass