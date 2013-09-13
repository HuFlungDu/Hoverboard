import wx
import time
import datetime
import os
import tempfile
import clippacloud
import struct
import clipboard

content = None


def waitfor_clip_content(cp):
    while True:
        content = get_clip_content(cp)
        if content:
            return content
        time.sleep(1)

def get_clip_content(cp):
    global content
    if cp.open():
        available = cp.get_available()
        if available == clipboard.CP_TEXT:
            newcontent = cp.get_data()
            if newcontent != content:
                content = newcontent
                cp.close()
                return content
        elif available == clipboard.CP_IMAGE:
            image = cp.get_data()
            if isinstance(content,clipboard.Image) and content != image: #(content.GetData() != image.GetData()):
                content = image
                cp.close()
                return content
            elif not isinstance(content,clipboard.Image):
                content = image
                cp.close()
                return content
        cp.close()
        return None

    else:
        cp.close()
        return None


def catch_clip(cp,backend):
    content = waitfor_clip_content(cp)
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

def try_catch_clip(cp,backend):
    content = get_clip_content(cp)
    now = datetime.datetime.utcnow()
    filename = str(now)
    if isinstance(content,clipboard.Image):
        filename += ".png"
        data = content.get_data()
        # if len(data) < clippacloud.config.max_size:
        #     backend.save_data(data,filename)
        return data, filename
        # return True
        
    elif isinstance(content,(str,unicode)):
        filename += ".txt"
        # if len(content) < clippacloud.config.max_size:
        #     backend.save_data(content,filename)
        return content, filename
        # return True
    # return False