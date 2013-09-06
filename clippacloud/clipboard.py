import sys
import os
import StringIO

_PY3 = sys.version_info[0] > 2
if _PY3:
    unicode = str
    xrange = range

try:
    # Linux/BSD or Mac
    if os.name == "posix":
        # Mac
        if sys.platform == "darwin":
            import Foundation
            import AppKit
            raise Exception
            #Not implemented yet
            _backend = "objc"
        # Linux/BSD
        else:
            # try:
            #     from gi.repository import Gtk, Gdk, GdkPixbuf,GObject
            #     _backend="gtk3"
            # except:
            # Gtk 3 is acting funny with the clipboard. Timeout until it behaves.
            import gtk
            _backend="gtk2"

    # Windows
    elif os.name == "nt":
        raise Exception
        _backend="win32"
except:
    # wx as a fallback, won't work if you aren't using wx as your main GUI
    import wx
    _backend = "wx"

def chunked(array,n):
    return [array[i:i+n] for i in xrange(0, len(array), n)]

CP_TEXT, CP_IMAGE = cp_data_types = xrange(2)

class Image(object):
    # We're using a png file now. Because getting the data into the right format for raw pixels was just awful.
    def __init__(self, data):
        if _backend == "gtk2":
            if isinstance(data,gtk.gdk.Pixbuf):
                self._image = data
            else:
                loader = gtk.gdk.PixbufLoader()
                loader.write(data)
                loader.close()
                self._image = loader.get_pixbuf()

            # if alpha is not None:
            #     data = "".join(map("".join,zip(chunked(data,3),alpha)))
            # if alpha is not None:
            #     data = "".join(map("".join,zip(chunked(data,3),alpha)))
            # stride_length = 0
            # if (len(data) > width*height*4):
            #     stride_length = (len(data)-(width*height*4))/height
            # elif (len(data) > width*height*3 and 
            #       len(data) != width*height*4):
            #     stride_length = (len(data)-(width*height*3))/height

            # if len(data) == width*height*3:
            #     stride = width*3
            #     has_alpha = False
            # elif len(data) == width*height*4:
            #     stride = width*4
            #     has_alpha = True
            # elif len(data) == (width*3+stride_length)*height:
            #     stride = width*3+stride_length
            #     has_alpha = False
            # elif len(data) == (width*4+stride_length)*height:
            #     stride = width*4+stride_length
            #     has_alpha = True
            # else:
            #     print width,height,stride_length, len(data), len(alpha)

            # self._image = gtk.gdk.pixbuf_new_from_data(data,gtk.gdk.COLORSPACE_RGB,has_alpha,8,width,height,stride)
        elif _backend == "gtk3":
            if isinstance(data,GdkPixbuf.Pixbuf):
                self._image = data
            else:
                #Later
                loader = gtk.gdk.PixbufLoader()
                loader.write(data)
                loader.close()
                self._image = loader.get_pixbuf()
            # if alpha is not None:
            #     data = "".join(map("".join,zip(chunked(data,3),alpha)))
            # stride_length = 0
            # if (len(data) > width*height*4):
            #     stride_length = (len(data)-(width*height*4))/height
            # elif (len(data) > width*height*3 and 
            #       len(data) != width*height*4):
            #     stride_length = (len(data)-(width*height*3))/height

            # if len(data) == width*height*3:
            #     stride = width*3
            #     has_alpha = False
            # elif len(data) == width*height*4:
            #     stride = width*4
            #     has_alpha = True
            # elif len(data) == (width*3+stride_length)*height:
            #     stride = width*3+stride_length
            #     has_alpha = False
            # elif len(data) == (width*4+stride_length)*height:
            #     stride = width*4+stride_length
            #     has_alpha = True
            # else:
            #     print width,height,stride_length, len(data)
            # self._image = GdkPixbuf.Pixbuf.new_from_data(data,GdkPixbuf.Colorspace.RGB,has_alpha,8,width,height,stride)
        elif _backend == "wx":
            if isinstance(data,wx.Bitmap):
                self._image = data
            else:
                sio = StringIO.StringIO(data)
                self._image = wx.ImageFromStream(sio, wx.BITMAP_TYPE_PNG)
                sio.close()
            # if alpha is not None:
            #     self._image = wx.ImageFromDataWithAlpha(width,height,data,alpha)
            # elif len(data) == width*height*4:
            #     data, alpha = reduce(lambda x, y: (x[0]+y[0],x[1]+y[1]),map(lambda x: chunked(x,3),chunked(data,4)),("",""))
            #     self._image = wx.ImageFromDataWithAlpha(width,height,data,alpha)
            # elif len(data) == width*height*3:
            #     self._image = wx.ImageFromData(width,height,data)
            # else:
            #     raise ValueError("Invalid image data")
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    def width():
        doc = "The image's width."
        def fget(self):
            if _backend == "gtk2":
                return self._image.get_width()
            elif _backend == "gtk3":
                return self._image.get_width()
            elif _backend == "wx":
                return self._image.GetWidth()
            elif _backend == "win32":
                pass
            elif _backend == "objc":
                pass
            return None
        return locals()
    width = property(**width())

    def height():
        doc = "The image's height."
        def fget(self):
            if _backend == "gtk2":
                return self._image.get_height()
            elif _backend == "gtk3":
                return self._image.get_height()
            elif _backend == "wx":
                return self._image.GetHeight()
            elif _backend == "win32":
                pass
            elif _backend == "objc":
                pass
            return None
        return locals()
    height = property(**height())

    def get_data(self):
        if _backend == "gtk2":
            sio = StringIO.StringIO()
            self._image.save_to_callback(sio.write,"png")
            data = sio.getvalue()
            sio.close()
            return data
            #return self._image.get_pixels()
        elif _backend == "gtk3":
            sio = StringIO.StringIO()
            self._image.save_to_callback(sio.write,"png")
            data = sio.getvalue()
            sio.close()
            return data
            #return self._image.get_pixels()
        elif _backend == "wx":
            sio = StringIO.StringIO()
            self._image.SaveStream(sio,wx.BITMAP_TYPE_PNG)
            data = sio.getvalue()
            sio.close()
            return data
            #return self._image.GetData()
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    # def get_alpha_data(self):
    #     if _backend == "gtk2":
    #         return ""
    #     elif _backend == "gtk3":
    #         return ""
    #     elif _backend == "wx":
    #         return self._image.GetAlphaData()
    #     elif _backend == "win32":
    #         pass
    #     elif _backend == "objc":
    #         pass

    # def has_alpha(self):
    #     if _backend == "gtk2":
    #         return False
    #     elif _backend == "gtk3":
    #         return False
    #     elif _backend == "wx":
    #         return self._image.HasAlpha()
    #     elif _backend == "win32":
    #         pass
    #     elif _backend == "objc":
    #         pass

    def __eq__(self,other):
        return self.get_data() == other.get_data()
        if _backend == "gtk2":
            return self.get_data() == other.get_data()
        elif _backend == "gtk3":
            return self.get_data() == other.get_data()
        elif _backend == "wx":
            # wx has weird handling of images, the same image from the clipboard will change data over time.
            # Big reason why I'm making this.
            return self.width == other.width and self.height == other.height
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    def __ne__(self,other):
        return not self == other
        return self.get_data() != other.get_data()
        if _backend == "gtk2":
            # I think this is because I'm sending in the data wrong.
            return self.width != other.width or self.height != other.height
            return ((self._image.get_pixels_array() != other._image.get_pixels_array()) is True 
                    or (self._image.get_pixels_array() != other._image.get_pixels_array()).any())
        elif _backend == "gtk3":
            return self._image.get_pixels() != other.get_data()
        elif _backend == "wx":
            # wx has weird handling of images, the same image from the clipboard will change data over time.
            # Big reason why I'm making this.
            return self.width != other.width or self.height != other.height
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

class Clipboard(object):
    def __init__(self):
        if _backend == "gtk2":
            self._clipboard = gtk.clipboard_get()
        elif _backend == "gtk3":
            self._clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        elif _backend == "wx":
            self._clipboard = wx.Clipboard.Get()
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    def open(self):
        if _backend == "gtk2":
            return True
        elif _backend == "gtk3":
            return True
        elif _backend == "wx":
            return self._clipboard.Open()
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    def close(self):
        if _backend == "gtk2":
            return True
        elif _backend == "gtk3":
            return True
        elif _backend == "wx":
            return self._clipboard.Close()
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    def get_available(self):
        if _backend == "gtk2":
            if self._clipboard.wait_is_text_available():
                return CP_TEXT
            elif self._clipboard.wait_is_image_available():
                return CP_IMAGE
            return None
        elif _backend == "gtk3":
            if self._clipboard.wait_is_text_available():
                return CP_TEXT
            elif self._clipboard.wait_is_image_available():
                return CP_IMAGE
            return None
        elif _backend == "wx":
            text_data = wx.TextDataObject()
            if self._clipboard.GetData(text_data):
                return CP_TEXT
            bitmap_data = wx.BitmapDataObject()
            if self._clipboard.GetData(bitmap_data):
                return CP_IMAGE
            return None
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    def get_data(self):
        if _backend == "gtk2":
            if self._clipboard.wait_is_text_available():
                return unicode(self._clipboard.wait_for_text())
            elif self._clipboard.wait_is_image_available():
                image = self._clipboard.wait_for_image()
                return Image(image)
        elif _backend == "gtk3":
            if self._clipboard.wait_is_text_available():
                return unicode(self._clipboard.wait_for_text())
            elif self._clipboard.wait_is_image_available():
                image =  self._clipboard.wait_for_image()
                return Image(image)
        elif _backend == "wx":
            text_data = wx.TextDataObject()
            if self._clipboard.GetData(text_data):
                return unicode(text_data.GetText())
            bitmap_data = wx.BitmapDataObject()
            if self._clipboard.GetData(bitmap_data):
                image = bitmap_data.GetBitmap()
                return Image(image)
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    def set_data(self,data):
        if _backend == "gtk2":
            if isinstance(data,(unicode,str)):
                self._clipboard.set_text(data)
            elif isinstance(data,Image):
                self._clipboard.set_image(data._image)
        elif _backend == "gtk3":
            if isinstance(data,(unicode,str)):
                self._clipboard.set_text(str(data),-1)
            elif isinstance(data,Image):
                self._clipboard.set_image(data._image)
        elif _backend == "wx":
            if isinstance(data,(unicode,str)):
                data = wx.TextDataObject(data)
            elif isinstance(data,Image):
                data = wx.BitmapDataObject(data._image.ConvertToBitmap())
            self._clipboard.AddData(data)
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass

    def flush(self):
        if _backend == "gtk2":
            self._clipboard.store()
        elif _backend == "gtk3":
            self._clipboard.store()
        elif _backend == "wx":
            self._clipboard.Flush()
        elif _backend == "win32":
            pass
        elif _backend == "objc":
            pass