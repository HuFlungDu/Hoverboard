from clippacloud import exceptions
from clippacloud import clipcatcher
import clippacloud
import wx
import tempfile
import os
import StringIO
import struct

def set_clipboard_from_cloud(cp):
    path = sorted(clippacloud.backend.list_files(), key=lambda x: x.modified, reverse=True)[0].path
    data = clippacloud.backend.get_file_data(path)
    if path.endswith(".txt"):
        clipcatcher.content = data
        data = wx.TextDataObject(data)
        cp.Open()
        cp.AddData(data)
        cp.Close()
    elif path.endswith("bmp"):
        width = struct.unpack(">L",data[:4])[0]
        height = struct.unpack(">L",data[4:8])[0]
        if len(data) > 8+width*height*3:
            image = wx.ImageFromDataWithAlpha(width,height,data[8:8+width*height*3],data[8+width*height*3:8+width*height*3 + width*height])
        else:
            image = wx.ImageFromData(width,height,data[8:8+width*height*3])            
        clipcatcher.content = image
        data = wx.BitmapDataObject(image.ConvertToBitmap())
        cp.Open()
        cp.AddData(data)
        cp.Close()
