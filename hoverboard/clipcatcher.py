import wx
import time
import datetime
import os
import hoverboard
from hoverboard import clipboard

content = None

def get_clip_content(cp, force=False):
    global content
    if cp.open():
        available = cp.get_available()
        if available == clipboard.CP_TEXT:
            newcontent = cp.get_data()
            if newcontent != content or force:
                content = newcontent
                cp.close()
                return content
        elif available == clipboard.CP_IMAGE:
            image = cp.get_data()
            if isinstance(content,clipboard.Image) and content != image or force: #(content.GetData() != image.GetData()):
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

def try_catch_clip(cp, force=False):
    content = get_clip_content(cp, force)
    if isinstance(content,clipboard.Image):
        return content.get_data(), "png"
        
    elif isinstance(content,(str,unicode)):
        return content, "txt"