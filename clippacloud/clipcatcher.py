import wx
import time
import datetime
import os
import tempfile
import clippacloud
import struct

content = None


def waitfor_clip_content(clipboard):
    while True:
        content = get_clip_content(clipboard)
        if content:
            return content
        time.sleep(1)

def get_clip_content(clipboard):
    global content
    if clipboard.Open():
        text_data = wx.TextDataObject()
        if clipboard.GetData(text_data):
            newcontent = text_data.GetText()
            if newcontent != content:
                content = newcontent
                clipboard.Close()
                return content
        bitmap_data = wx.BitmapDataObject()
        if clipboard.GetData(bitmap_data):
            image = bitmap_data.GetBitmap().ConvertToImage()
            # This is dumb, but for some reason the bitmap data is coming in differently even though it's all the same bitmap
            # No idea. Comparing height and width for now.
            if isinstance(content,wx.Image) and (content.GetWidth() != image.GetWidth()) and (content.GetHeight() != image.GetHeight()): #(content.GetData() != image.GetData()):
                content = image
                clipboard.Close()
                return content
            elif not isinstance(content,wx.Image):
                content = image
                clipboard.Close()
                return content
        clipboard.Close()
        return None

    else:
        clipboard.Close()
        return None


def catch_clip(clipboard,backend):
    content = waitfor_clip_content(clipboard)
    now = datetime.datetime.utcnow()
    filename = str(now)
    if isinstance(content,gtk.gdk.Pixbuf):
        filename += ".png"
        tmpfile, tmppath = tempfile.mkstemp()
        os.fdopen(tmpfile,"wb").close()
        content.save(tmppath,"png")
        with open(tmppath,"rb") as pngfile:
            data = pngfile.read()
        os.remove(tmppath)
        if len(data) < clippacloud.config.max_size:
            backend.save_data(data,filename)
        
    elif isinstance(content,(str,unicode)):
        filename += ".txt"
        if len(content) < clippacloud.config.max_size:
            backend.save_data(content,filename)

def try_catch_clip(clipboard,backend):
    content = get_clip_content(clipboard)
    now = datetime.datetime.utcnow()
    filename = str(now)
    if isinstance(content,wx.Image):
        filename += ".bmp"
        data = struct.pack(">L",content.GetWidth()) + struct.pack(">L",content.GetHeight()) + content.GetData()
        if content.HasAlpha():
            data += content.GetAlphaData()
        if len(data) < clippacloud.config.max_size:
            backend.save_data(data,filename)
        return True
        
    elif isinstance(content,(str,unicode)):
        filename += ".txt"
        if len(content) < clippacloud.config.max_size:
            backend.save_data(content,filename)
        return True
    return False