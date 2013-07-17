from clippacloud import exceptions
#from clippacloud import sendevent
import clippacloud
#import gtk
import wx
import tempfile
import os

# def paste():
#     cp = gtk.clipboard_get()
#     #set_clipboard_from_cloud(cp)
#     sendevent.send_key(keycodes.k_v,keycodes.mod_control)

# def paste_terminal():
#     try:
#         cp = gtk.clipboard_get()
#         #set_clipboard_from_cloud(cp)
#         sendevent.send_key(keycodes.k_v,keycodes.mod_control|keycodes.mod_shift)
#     except Exception as e:
#         print e

def set_clipboard_from_cloud(cp):
    path = sorted(clippacloud.backend.list_files(), key=lambda x: x.modified, reverse=True)[0].path
    data = clippacloud.backend.get_file_data(path)
    if path.endswith(".txt"):
        data = wx.TextDataObject(data)
        cp.AddData(data)
    elif path.endswith("png"):
        tmpfile, tmppath = tempfile.mkstemp()
        with os.fdopen(tmpfile,"wb") as outfile:
            outfile.write(data)
        with open(tempfile,"rb") as infile:
            image = wx.Image.LoadFile(infile,wx.BITMAP_TYPE_PNG)
        data = wx.BitmapDataObject(image.ConvertToBitmap())
        cp.set_image(gtk.gdk.pixbuf_new_from_file(tmppath))
        os.remove(tmppath)
    
