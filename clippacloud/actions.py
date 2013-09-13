from clippacloud import exceptions
from clippacloud import clipcatcher
import clippacloud
import wx
import tempfile
import os
import StringIO
import struct
import clipboard

def set_clipboard_from_cloud(cp,data,path):
    if path.endswith(".txt"):
        clipcatcher.content = data
        cp.open()
        cp.set_data(data)
        cp.close()
    elif path.endswith(".png"):
        # width = struct.unpack(">L",data[:4])[0]
        # height = struct.unpack(">L",data[4:8])[0]
        # if len(data) > 8+width*height*3:
        #     image = clipboard.Image(width,height,data[8:8+width*height*3],data[8+width*height*3:8+width*height*3 + width*height])
        # else:
        #     image = clipboard.Image(width,height,data[8:8+width*height*3])    
        image = clipboard.Image(data)
        clipcatcher.content = image
        cp.open()
        cp.set_data(image)
        cp.close()
