import gtk
import pygtk
pygtk.require("2.0")
import time
import datetime
import os
import tempfile

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
    if clipboard.wait_is_text_available():
        newcontent = clipboard.wait_for_text()
        if newcontent != content:
            content = newcontent
            return content
    elif clipboard.wait_is_image_available():
        newcontent = clipboard.wait_for_image()
        if (isinstance(content,gtk.gdk.Pixbuf) and 
                #Weird bug where sometimes comparing two numpy arrays returns a bool value. No idea where that comes from
                ((newcontent.get_pixels_array() != content.get_pixels_array()) is True 
                or (newcontent.get_pixels_array() != content.get_pixels_array()).any())):
            content = newcontent
            return content
        elif not isinstance(content,gtk.gdk.Pixbuf):
            content = newcontent
            return content
        return None


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
        backend.save_data(data,filename)
        
    elif isinstance(content,str):
        filename += ".txt"
        backend.save_data(content,filename)
        #with open(path,'w') as clipfile:
        #    clipfile.write(content)

def try_catch_clip(clipboard,backend):
    content = get_clip_content(clipboard)
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
        backend.save_data(data,filename)
        return True
        
    elif isinstance(content,str):
        filename += ".txt"
        backend.save_data(content,filename)
        return True
        #with open(path,'w') as clipfile:
        #    clipfile.write(content)
    return False