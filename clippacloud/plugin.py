import wx
import os
import imp

#Only one control so far because this is the only one I need. Kind of defeats the purpose of a plugin system, but there you go.
LINK_CONTROL, = xrange(1)

(RESPONSE_ACCEPT,RESPONSE_NO,
 RESPONSE_APPLY,RESPONSE_NONE,
 RESPONSE_CANCEL,RESPONSE_OK,
 RESPONSE_CLOSE,RESPONSE_REJECT,
 RESPONSE_YES) = xrange(9)

response_map = {wx.ID_OK:		RESPONSE_OK,
				wx.ID_YES:		RESPONSE_YES,
				wx.ID_NO:		RESPONSE_NO,
				wx.ID_CANCEL:	RESPONSE_CANCEL,
				wx.ID_CLOSE:	RESPONSE_CLOSE,
				wx.ID_APPLY:	RESPONSE_APPLY,
				wx.ID_NONE:		RESPONSE_NONE}

BACKEND_PLUGIN, = plugin_types = xrange(1)


class FileDescription(object):
    def __init__(self,path,modified,size):
        self.path = path
        self.modified = modified
        self.size = size
        pass

class PluginWindow(object):
    def __init__(self,window):
        self.window = window
        self.controls = []

    def destroy(self):
        self.window.Destroy()

    def hide(self):
        self.window.Show(False)

    def show(self):
        self.window.Show(True)

    #Used later when we'll need to get info back from the various controls
    def add_control(self,control):
        self.controls.append(control)

    #In the future, return data from controls, e.g. username and password
    def get_controls_data(self):
        pass

    #Just in case
    def __getattr__(self,name):
        return getattr(self.dialog,name)

class PluginDialog(PluginWindow):
    def run(self):
        return response_map.get(self.window.ShowModal(),None)

def make_dialog(definition):
    window = wx.Dialog(None,-1,definition["title"])
    dialog = PluginDialog(window)
    panel = wx.Panel(window, -1)
    for control in definition["controls"]:
        if control["type"] == LINK_CONTROL:
            wx_control = wx.HyperlinkCtrl(panel,-1,control["text"],control["url"])
        dialog.add_control((control["type"],wx_control))
    mainvbox = wx.BoxSizer(wx.VERTICAL)
    ok_button = wx.Button(panel, wx.ID_OK)
    cancel_button = wx.Button(panel, wx.ID_CANCEL)
    button_sizer = wx.StdDialogButtonSizer()
    button_sizer.AddButton(ok_button)
    button_sizer.AddButton(cancel_button)
    button_sizer.Realize()
    if button_sizer:
        mainvbox.Add(button_sizer,wx.ALIGN_RIGHT)
    border = wx.BoxSizer()
    border.Add(mainvbox, 0, wx.ALL, 15)
    panel.SetSizerAndFit(border)
    window.Fit()
    return dialog

def get_plugins(directory="plugins"):
    filelist = os.listdir(directory)
    plugins = {}
    for filename in filelist:
        try:
            impfile, imppath, impdescription = imp.find_module(filename.split(".")[0],[directory])
            module = imp.load_module("{}_plugin".format(filename.split(".")[0]), 
                                     impfile, imppath, impdescription)

            if module.plugin_name not in plugins.setdefault(module.plugin_type, {}):
                plugins[module.plugin_type][module.plugin_name] = module.Backend
        except Exception as e:
            print e
        finally:
            try:
                impfile.close()
            except:
                pass 
    return plugins