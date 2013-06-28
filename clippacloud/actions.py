from clippacloud import exceptions
from clippacloud import sendevent
from clippacloud import keycodes
import clippacloud
import gtk
import tempfile
import os

def paste():
    cp = gtk.clipboard_get()
    #set_clipboard_from_cloud(cp)
    sendevent.send_key(keycodes.k_v,keycodes.mod_control)

def paste_terminal():
    try:
        cp = gtk.clipboard_get()
        #set_clipboard_from_cloud(cp)
        sendevent.send_key(keycodes.k_v,keycodes.mod_control|keycodes.mod_shift)
    except Exception as e:
        print e

def set_clipboard_from_cloud(cp):
    path = sorted(clippacloud.backend.list_files(), key=lambda x: x.modified, reverse=True)[0].path
    data = clippacloud.backend.get_file_data(path)
    if path.endswith(".txt"):
        cp.set_text(data)
    elif path.endswith("png"):
        tmpfile, tmppath = tempfile.mkstemp()
        with os.fdopen(tmpfile,"wb") as outfile:
            outfile.write(data)
        cp.set_image(gtk.gdk.pixbuf_new_from_file(tmppath))
        os.remove(tmppath)
    
