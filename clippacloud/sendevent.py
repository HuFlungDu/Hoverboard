from clippacloud import exceptions
from clippacloud import keycodes
import time

try:
    import win32api
    __backend = "win32"
except ImportError:
    try:
        import Xlib
        import Xlib.X
        import Xlib.protocol
        import Xlib.display
        import gtk
        import evdev
        __backend = "Xorg"
    except ImportError:
        __backend == "Mac"
        #raise exceptions.BackendNotFoundError("Backend not found for send event")
if __backend == "Xorg":
    def send_key(key, mask):
        start = time.time()
        with evdev.UInput() as __uinput:
        # start = time.time()
        # d = Xlib.display.Display()
        # focused = d.get_input_focus().focus
        # r = d.screen().root
        # keycode = d.keysym_to_keycode(gtk.keysyms.Super_L)
        # Xlib.ext.xtest.fake_input(d,Xlib.X.KeyRelease, keycode)
        # d.sync()
        # if mask & keycodes.mod_shift:
        #     keycode = d.keysym_to_keycode(gtk.keysyms.Shift_L)
        #     Xlib.ext.xtest.fake_input(d,Xlib.X.KeyPress, keycode)

        # if mask & keycodes.mod_control:
        #     keycode = d.keysym_to_keycode(gtk.keysyms.Control_L)
        #     Xlib.ext.xtest.fake_input(d,Xlib.X.KeyPress, keycode)

        # if mask & keycodes.mod_super:
        #     keycode = d.keysym_to_keycode(gtk.keysyms.Super_L)
        #     Xlib.ext.xtest.fake_input(d,Xlib.X.KeyPress, keycode)

        # if mask & keycodes.mod_alt:
        #     keycode = d.keysym_to_keycode(gtk.keysyms.Alt_L)
        #     Xlib.ext.xtest.fake_input(d,Xlib.X.KeyPress, keycode)

        # keycode = d.keysym_to_keycode(key)
        # Xlib.ext.xtest.fake_input(d,Xlib.X.KeyPress, keycode)
        # d.sync()
        # Xlib.ext.xtest.fake_input(d,Xlib.X.KeyRelease, d.keysym_to_keycode(key))
        # d.sync()

        # if mask & keycodes.mod_shift:
        #     keycode = d.keysym_to_keycode(gtk.keysyms.Shift_L)
        #     Xlib.ext.xtest.fake_input(d,Xlib.X.KeyRelease, keycode)

        # if mask & keycodes.mod_control:
        #     keycode = d.keysym_to_keycode(gtk.keysyms.Control_L)
        #     Xlib.ext.xtest.fake_input(d,Xlib.X.KeyRelease, keycode)

        # if mask & keycodes.mod_super:
        #     keycode = d.keysym_to_keycode(gtk.keysyms.Super_L)
        #     Xlib.ext.xtest.fake_input(d,Xlib.X.KeyRelease, keycode)

        # if mask & keycodes.mod_alt:
        #     keycode = d.keysym_to_keycode(gtk.keysyms.Alt_L)
        #     Xlib.ext.xtest.fake_input(d,Xlib.X.KeyRelease, keycode)

        # d.sync()
            if mask & keycodes.mod_shift:
                __uinput.write(evdev.ecodes.EV_KEY, keycodes.i_mod_shift, 1)

            if mask & keycodes.mod_control:
                __uinput.write(evdev.ecodes.EV_KEY, keycodes.i_mod_control, 1)

            if mask & keycodes.mod_super:
                __uinput.write(evdev.ecodes.EV_KEY, keycodes.i_mod_super, 1)

            if mask & keycodes.mod_alt:
                __uinput.write(evdev.ecodes.EV_KEY, keycodes.i_mod_alt, 1)

            __uinput.write(evdev.ecodes.EV_KEY, keycodes._keymap[key], 1)
            __uinput.write(evdev.ecodes.EV_KEY, keycodes._keymap[key], 0)

            if mask & keycodes.mod_shift:
                __uinput.write(evdev.ecodes.EV_KEY, keycodes.i_mod_shift, 0)

            if mask & keycodes.mod_control:
                __uinput.write(evdev.ecodes.EV_KEY, keycodes.i_mod_control, 0)

            if mask & keycodes.mod_super:
                __uinput.write(evdev.ecodes.EV_KEY, keycodes.i_mod_super, 0)

            if mask & keycodes.mod_alt:
                __uinput.write(evdev.ecodes.EV_KEY, keycodes.i_mod_alt, 0)
            __uinput.syn()

elif __backend == "win32":
    def send_key(key,mask):
        pass

elif __backend == "Mac":
    def send_key(key,mask):
        pass