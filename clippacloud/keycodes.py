import string
from clippacloud import exceptions

__backend = None
try:
    import win32con
    __backend = "win32"
except ImportError:
    try:
        import Xlib
        import gtk
        import evdev
        __backend = "Xorg"
    except:
        __backend = "Mac"
        #raise exceptions.BackendNotFoundError("Backend not found for keycodes")

if __backend == "win32":
    mod_shift,mod_control,mod_alt,mod_super = win32con.MOD_SHIFT, win32con.MOD_CONTROL, win32con.MOD_ALT, win32con.MOD_WIN
    k_Up, k_Down, k_Left, k_Right = win32con.VK_UP,win32con.VK_DOWN,win32con.VK_LEFT,win32con.VK_RIGHT
    k_a,k_b,k_c,k_d,k_e,k_f,k_g,k_h,k_i,k_j,k_k,k_l,k_m,k_n,k_o,k_p,k_q,k_r,k_s,k_t,k_u,k_v,k_w,k_x,k_y,k_z = (ord(x) for x in string.ascii_uppercase)
    k_Comma, k_Period = 0xBC, 0xBE
    k_1,k_2,k_3,k_4,k_5,k_6,k_7,k_8,k_9,k_0 = (ord(x) for x in "1234567890")
    k_Home, k_End, k_PgUp, k_PgDn, k_Insert, k_Space, k_Return, k_Enter,k_BackSpace,k_Tab,k_Clear,k_Pause,k_Escape,k_Delete = win32con.VK_HOME, win32con.VK_END, win32con.VK_PRIOR, win32con.VK_NEXT, win32con.VK_INSERT, win32con.VK_SPACE, win32con.VK_RETURN, win32con.VK_RETURN, win32con.VK_BACK,win32con.VK_TAB,win32con.VK_CLEAR,win32con.VK_PAUSE,win32con.VK_ESCAPE,win32con.VK_DELETE
    k_KP_0,k_KP_1,k_KP_2,k_KP_3,k_KP_4,k_KP_5,k_KP_6,k_KP_7,k_KP_8,k_KP_9 = win32con.VK_NUMPAD0, win32con.VK_NUMPAD1, win32con.VK_NUMPAD2, win32con.VK_NUMPAD3, win32con.VK_NUMPAD4, win32con.VK_NUMPAD5, win32con.VK_NUMPAD6, win32con.VK_NUMPAD7, win32con.VK_NUMPAD8, win32con.VK_NUMPAD9
    k_F1,k_F2,k_F3,k_F4,k_F5,k_F6,k_F7,k_F8,k_F9,k_F10,k_F11,k_F12,k_F13,k_F14,k_F15,k_F16,k_F17,k_F18,k_F19,k_F20,k_F21,k_F22,k_F23,k_24 = win32con.VK_F1,win32con.VK_F2,win32con.VK_F3,win32con.VK_F4,win32con.VK_F5,win32con.VK_F6,win32con.VK_F7,win32con.VK_F8,win32con.VK_F9,win32con.VK_F10,win32con.VK_F11,win32con.VK_F12,win32con.VK_F13,win32con.VK_F14,win32con.VK_F15,win32con.VK_F16,win32con.VK_F17,win32con.VK_F18,win32con.VK_F19,win32con.VK_F20,win32con.VK_F21,win32con.VK_F22,win32con.VK_F23,win32con.VK_F24

elif __backend == "Xorg":
    mod_shift,mod_control,mod_alt,mod_super = gtk.gdk.SHIFT_MASK, gtk.gdk.CONTROL_MASK,gtk.gdk.MOD1_MASK,gtk.gdk.SUPER_MASK
    k_Up, k_Down, k_Left, k_Right = gtk.keysyms.Up,gtk.keysyms.Down,gtk.keysyms.Left,gtk.keysyms.Right
    k_a,k_b,k_c,k_d,k_e,k_f,k_g,k_h,k_i,k_j,k_k,k_l,k_m,k_n,k_o,k_p,k_q,k_r,k_s,k_t,k_u,k_v,k_w,k_x,k_y,k_z = (ord(x) for x in string.ascii_uppercase)
    k_Comma, k_Period = gtk.keysyms.comma,gtk.keysyms.period
    k_1,k_2,k_3,k_4,k_5,k_6,k_7,k_8,k_9,k_0 = (ord(x) for x in "1234567890")
    k_Home, k_End, k_PgUp, k_PgDn, k_Insert, k_Space, k_Return, k_Enter,k_BackSpace,k_Tab,k_Clear,k_Pause,k_Escape,k_Delete = gtk.keysyms.Home, gtk.keysyms.End, gtk.keysyms.Page_Up, gtk.keysyms.Page_Down, gtk.keysyms.Insert, gtk.keysyms.space, gtk.keysyms.Return, gtk.keysyms.Return,gtk.keysyms.BackSpace,gtk.keysyms.Tab,gtk.keysyms.Clear,gtk.keysyms.Pause,gtk.keysyms.Escape,gtk.keysyms.Delete
    k_KP_0,k_KP_1,k_KP_2,k_KP_3,k_KP_4,k_KP_5,k_KP_6,k_KP_7,k_KP_8,k_KP_9 = gtk.keysyms.KP_0,gtk.keysyms.KP_1,gtk.keysyms.KP_2,gtk.keysyms.KP_3,gtk.keysyms.KP_4,gtk.keysyms.KP_5,gtk.keysyms.KP_6,gtk.keysyms.KP_7,gtk.keysyms.KP_8,gtk.keysyms.KP_9
    k_F1,k_F2,k_F3,k_F4,k_F5,k_F6,k_F7,k_F8,k_F9,k_F10,k_F11,k_F12,k_F13,k_F14,k_F15,k_F16,k_F17,k_F18,k_F19,k_F20,k_F21,k_F22,k_F23,k_F24 = gtk.keysyms.F1,gtk.keysyms.F2,gtk.keysyms.F3,gtk.keysyms.F4,gtk.keysyms.F5,gtk.keysyms.F6,gtk.keysyms.F7,gtk.keysyms.F8,gtk.keysyms.F9,gtk.keysyms.F10,gtk.keysyms.F11,gtk.keysyms.F12,gtk.keysyms.F13,gtk.keysyms.F14,gtk.keysyms.F15,gtk.keysyms.F16,gtk.keysyms.F17,gtk.keysyms.F18,gtk.keysyms.F19,gtk.keysyms.F20,gtk.keysyms.F21,gtk.keysyms.F22,gtk.keysyms.F23,gtk.keysyms.F24

    i_mod_shift,i_mod_control,i_mod_alt,i_mod_super = evdev.ecodes.KEY_LEFTSHIFT, evdev.ecodes.KEY_LEFTCTRL,evdev.ecodes.KEY_LEFTALT, evdev.ecodes.KEY_LEFTMETA #NotImplemented?
    i_k_Up, i_k_Down, i_k_Left, i_k_Right = evdev.ecodes.KEY_UP,evdev.ecodes.KEY_DOWN,evdev.ecodes.KEY_LEFT,evdev.ecodes.KEY_RIGHT
    i_k_a,i_k_b,i_k_c,i_k_d,i_k_e,i_k_f,i_k_g,i_k_h,i_k_i,i_k_j,i_k_k,i_k_l,i_k_m,i_k_n,i_k_o,i_k_p,i_k_q,i_k_r,i_k_s,i_k_t,i_k_u,i_k_v,i_k_w,i_k_x,i_k_y,i_k_z = [eval("evdev.ecodes.KEY_"+x) for x in string.ascii_uppercase]
    i_k_Comma, i_k_Period = evdev.ecodes.KEY_COMMA, evdev.ecodes.KEY_DOT
    i_k_1,i_k_2,i_k_3,i_k_4,i_k_5,i_k_6,i_k_7,i_k_8,i_k_9,i_k_0 = [eval("evdev.ecodes.KEY_"+x) for x in "1234567890"]
    i_k_Home, i_k_End, i_k_PgUp, i_k_PgDn, i_k_Insert, i_k_Space, i_k_Return, i_k_Enter,i_k_BackSpace,i_k_Tab,i_k_Clear,i_k_Pause,i_k_Escape,i_k_Delete = evdev.ecodes.KEY_HOME, evdev.ecodes.KEY_END,evdev.ecodes.KEY_PAGEUP, evdev.ecodes.KEY_PAGEDOWN, evdev.ecodes.KEY_INSERT, evdev.ecodes.KEY_SPACE, evdev.ecodes.KEY_ENTER, evdev.ecodes.KEY_ENTER, evdev.ecodes.KEY_BACKSPACE, evdev.ecodes.KEY_TAB, evdev.ecodes.KEY_CLEAR, evdev.ecodes.KEY_PAUSE, evdev.ecodes.KEY_ESC, evdev.ecodes.KEY_DELETE
    i_k_KP_0,i_k_KP_1,i_k_KP_2,i_k_KP_3,i_k_KP_4,i_k_KP_5,i_k_KP_6,i_k_KP_7,i_k_KP_8,i_k_KP_9 = [eval("evdev.ecodes.KEY_KP"+x) for x in "1234567890"]
    i_k_F1,i_k_F2,i_k_F3,i_k_F4,i_k_F5,i_k_F6,i_k_F7,i_k_F8,i_k_F9,i_k_F10,i_k_F11,i_k_F12,i_k_F13,i_k_F14,i_k_F15,i_k_F16,i_k_F17,i_k_F18,i_k_F19,i_k_F20,i_k_F21,i_k_F22,i_k_F23,i_k_F24 = [eval("evdev.ecodes.KEY_F"+str(x)) for x in xrange(1,25)]

    _keymap = {mod_shift :i_mod_shift ,mod_control :i_mod_control ,mod_alt :i_mod_alt ,mod_super:i_mod_super,
               k_Up  :i_k_Up  ,k_Down  :i_k_Down  ,k_Left  :i_k_Left  ,k_Right:i_k_Right,
               k_a :i_k_a ,k_b :i_k_b ,k_c :i_k_c ,k_d :i_k_d ,k_e :i_k_e ,k_f :i_k_f ,k_g :i_k_g ,k_h :i_k_h ,k_i :i_k_i ,k_j :i_k_j ,k_k :i_k_k ,k_l :i_k_l ,k_m :i_k_m ,k_n :i_k_n ,k_o :i_k_o ,k_p :i_k_p ,k_q :i_k_q ,k_r :i_k_r ,k_s :i_k_s ,k_t :i_k_t ,k_u :i_k_u ,k_v :i_k_v ,k_w :i_k_w ,k_x :i_k_x ,k_y :i_k_y ,k_z:i_k_z,
               k_Comma  :i_k_Comma  ,k_Period:i_k_Period,
               k_1 :i_k_1 ,k_2 :i_k_2 ,k_3 :i_k_3 ,k_4 :i_k_4 ,k_5 :i_k_5 ,k_6 :i_k_6 ,k_7 :i_k_7 ,k_8 :i_k_8 ,k_9 :i_k_9 ,k_0:i_k_0,
               k_Home  :i_k_Home  ,k_End  :i_k_End  ,k_PgUp  :i_k_PgUp  ,k_PgDn  :i_k_PgDn  ,k_Insert  :i_k_Insert  ,k_Space  :i_k_Space  ,k_Return  :i_k_Return  ,k_Enter :i_k_Enter ,k_BackSpace :i_k_BackSpace ,k_Tab :i_k_Tab ,k_Clear :i_k_Clear ,k_Pause :i_k_Pause ,k_Escape :i_k_Escape ,k_Delete:i_k_Delete,
               k_KP_0 :i_k_KP_0 ,k_KP_1 :i_k_KP_1 ,k_KP_2 :i_k_KP_2 ,k_KP_3 :i_k_KP_3 ,k_KP_4 :i_k_KP_4 ,k_KP_5 :i_k_KP_5 ,k_KP_6 :i_k_KP_6 ,k_KP_7 :i_k_KP_7 ,k_KP_8 :i_k_KP_8 ,k_KP_9:i_k_KP_9,
               k_F1 :i_k_F1 ,k_F2 :i_k_F2 ,k_F3 :i_k_F3 ,k_F4 :i_k_F4 ,k_F5 :i_k_F5 ,k_F6 :i_k_F6 ,k_F7 :i_k_F7 ,k_F8 :i_k_F8 ,k_F9 :i_k_F9 ,k_F10 :i_k_F10 ,k_F11 :i_k_F11 ,k_F12 :i_k_F12 ,k_F13 :i_k_F13 ,k_F14 :i_k_F14 ,k_F15 :i_k_F15 ,k_F16 :i_k_F16 ,k_F17 :i_k_F17 ,k_F18 :i_k_F18 ,k_F19 :i_k_F19 ,k_F20 :i_k_F20 ,k_F21 :i_k_F21 ,k_F22 :i_k_F22 ,k_F23 :i_k_F23 ,k_F24:i_k_F24}

elif __backend == "Mac":
    mod_shift,mod_control,mod_alt,mod_super = gtk.gdk.SHIFT_MASK, gtk.gdk.CONTROL_MASK,gtk.gdk.MOD1_MASK,gtk.gdk.SUPER_MASK
    k_Up, k_Down, k_Left, k_Right = gtk.keysyms.Up,gtk.keysyms.Down,gtk.keysyms.Left,gtk.keysyms.Right
    k_a,k_b,k_c,k_d,k_e,k_f,k_g,k_h,k_i,k_j,k_k,k_l,k_m,k_n,k_o,k_p,k_q,k_r,k_s,k_t,k_u,k_v,k_w,k_x,k_y,k_z = (ord(x) for x in string.ascii_uppercase)
    k_Comma, k_Period = gtk.keysyms.comma,gtk.keysyms.period
    k_1,k_2,k_3,k_4,k_5,k_6,k_7,k_8,k_9,k_0 = (ord(x) for x in "1234567890")
    k_Home, k_End, k_PgUp, k_PgDn, k_Insert, k_Space, k_Return, k_Enter,k_BackSpace,k_Tab,k_Clear,k_Pause,k_Escape,k_Delete = gtk.keysyms.Home, gtk.keysyms.End, gtk.keysyms.Page_Up, gtk.keysyms.Page_Down, gtk.keysyms.Insert, gtk.keysyms.space, gtk.keysyms.Return, gtk.keysyms.Return,gtk.keysyms.BackSpace,gtk.keysyms.Tab,gtk.keysyms.Clear,gtk.keysyms.Pause,gtk.keysyms.Escape,gtk.keysyms.Delete
    k_KP_0,k_KP_1,k_KP_2,k_KP_3,k_KP_4,k_KP_5,k_KP_6,k_KP_7,k_KP_8,k_KP_9 = gtk.keysyms.KP_0,gtk.keysyms.KP_1,gtk.keysyms.KP_2,gtk.keysyms.KP_3,gtk.keysyms.KP_4,gtk.keysyms.KP_5,gtk.keysyms.KP_6,gtk.keysyms.KP_7,gtk.keysyms.KP_8,gtk.keysyms.KP_9
    k_F1,k_F2,k_F3,k_F4,k_F5,k_F6,k_F7,k_F8,k_F9,k_F10,k_F11,k_F12,k_F13,k_F14,k_F15,k_F16,k_F17,k_F18,k_F19,k_F20,k_F21,k_F22,k_F23,k_F24 = gtk.keysyms.F1,gtk.keysyms.F2,gtk.keysyms.F3,gtk.keysyms.F4,gtk.keysyms.F5,gtk.keysyms.F6,gtk.keysyms.F7,gtk.keysyms.F8,gtk.keysyms.F9,gtk.keysyms.F10,gtk.keysyms.F11,gtk.keysyms.F12,gtk.keysyms.F13,gtk.keysyms.F14,gtk.keysyms.F15,gtk.keysyms.F16,gtk.keysyms.F17,gtk.keysyms.F18,gtk.keysyms.F19,gtk.keysyms.F20,gtk.keysyms.F21,gtk.keysyms.F22,gtk.keysyms.F23,gtk.keysyms.F24