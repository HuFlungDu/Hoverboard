import hoverboard
from hoverboard import clipcatcher
from hoverboard import clipboard

def set_clipboard_from_cloud(cp,data,filedata):
    if filedata.path.endswith(".txt"):
        clipcatcher.content = data
        cp.open()
        cp.set_data(data)
        cp.close()
    elif filedata.path.endswith(".png"):
        image = clipboard.Image(data)
        clipcatcher.content = image
        cp.open()
        cp.set_data(image)
        cp.close()
