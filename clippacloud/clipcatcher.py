# import gtk
# import pygtk
#pygtk.require("2.0")
import wx
import time
import datetime
import os
import tempfile
from clippacloud import config

content = None

def waitfor_clip_content(clipboard):
    while True:
        #if clipboard.wait_is_uris_available:
        #    print "here"
        #    pass
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
            if isinstance(content,wx.Image) and content.GetData() != image.GetData():
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
        # if clipboard.wait_is_text_available():
        #     newcontent = clipboard.wait_for_text()
        #     if newcontent != content:
        #         content = newcontent
        #         return content
        # elif clipboard.wait_is_image_available():
        #     newcontent = clipboard.wait_for_image()
        #     if (isinstance(content,gtk.gdk.Pixbuf) and 
        #             #Weird bug where sometimes comparing two numpy arrays returns a bool value. No idea where that comes from
        #             ((newcontent.get_pixels_array() != content.get_pixels_array()) is True 
        #             or (newcontent.get_pixels_array() != content.get_pixels_array()).any())):
        #         content = newcontent
        #         return content
        #     elif not isinstance(content,gtk.gdk.Pixbuf):
        #         content = newcontent
        #         return content
        #     return None


def catch_clip(clipboard,backend):
    content = waitfor_clip_content(clipboard)
    now = datetime.datetime.now()
    #path = os.path.join(savepath,str(now))
    filename = str(now)
    if isinstance(content,gtk.gdk.Pixbuf):
        filename += ".png"
        tmpfile, tmppath = tempfile.mkstemp()
        os.fdopen(tmpfile,"wb").close()
        content.save(tmppath,"png")
        with open(tmppath,"rb") as pngfile:
            data = pngfile.read()
        os.remove(tmppath)
        if len(data) < config.max_size:
            backend.save_data(data,filename)
        
    elif isinstance(content,str):
        filename += ".txt"
        if len(content) < config.max_size:
            backend.save_data(content,filename)
        #with open(path,'w') as clipfile:
        #    clipfile.write(content)

def try_catch_clip(clipboard,backend):
    content = get_clip_content(clipboard)
    now = datetime.datetime.now()
    #path = os.path.join(savepath,str(now))
    filename = str(now)
    if isinstance(content,wx.Image):
        filename += ".png"
        tmpfile, tmppath = tempfile.mkstemp()
        os.fdopen(tmpfile,"wb").close()
        content.SaveFile(tmppath,wx.BITMAP_TYPE_PNG)
        with open(tmppath,"rb") as pngfile:
            data = pngfile.read()
        os.remove(tmppath)
        if len(data) < config.max_size:
            backend.save_data(data,filename)
        return True
        
    elif isinstance(content,(str,unicode)):
        filename += ".txt"
        if len(content) < config.max_size:
            backend.save_data(content,filename)
        return True
        #with open(path,'w') as clipfile:
        #    clipfile.write(content)
    return False