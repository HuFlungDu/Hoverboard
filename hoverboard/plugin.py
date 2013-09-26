import wx
import os
import imp
import functools
import collections
import logging
import datetime

#Only one control so far because this is the only one I need. Kind of defeats the purpose of a plugin system, but there you go.
LINK_CONTROL,TEXTINPUT_CONTROL = xrange(2)

control_defaults = {LINK_CONTROL:None,
                    TEXTINPUT_CONTROL: ""}

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
    def __init__(self,name,format,modified,size,is_dir,extra_data=None):
        self.name = name
        self.format = format
        self.modified = modified
        self.size = size
        self.is_dir = is_dir
        self.extra_data = extra_data

class Device(object):
    def __init__(self,name,last_checkin):
        self.name = name
        self.last_checkin = last_checkin

    def active():
        doc = "Whether device is currently active"
        def fget(self):
            timedelta = datetime.datetime.utcnow() - self.last_checkin
            return (timedelta.days * 86400 + timedelta.seconds)/60 < 20
        return locals()
    active = property(**active())

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
        control_change_bindings = {LINK_CONTROL: (None,None),
                                   TEXTINPUT_CONTROL: (wx.EVT_TEXT,functools.partial(self.text_input_value_changed, control=control[0]))}
        control[0]["value"] = control_defaults.get(control[0]["type"],None)
        binding = control_change_bindings.get(control[0]["type"],(None,None))
        if binding[0] is not None:
            control[1].Bind(binding[0],binding[1])
        self.controls.append(control[0])

    def text_input_value_changed(self,event,control):
        control["value"] = event.GetString()

    #In the future, return data from controls, e.g. username and password
    def get_controls_data(self):
        values = collections.OrderedDict()
        for control in self.controls:
            values[control["name"]]=control["value"]
        return values

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
    controls = []
    for control in definition["controls"]:
        if control["type"] == LINK_CONTROL:
            wx_control = wx.HyperlinkCtrl(panel,-1,control["text"],control["url"])
            controls.append(wx_control)
        elif control["type"] == TEXTINPUT_CONTROL:
            wx_control = wx.TextCtrl(panel,-1)
            label = wx.StaticText(panel,-1,control["label"])
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add(label)
            hbox.Add(wx_control,1,wx.EXPAND)
            controls.append(hbox)
        dialog.add_control((control,wx_control))
    mainvbox = wx.BoxSizer(wx.VERTICAL)
    for control in controls:
        mainvbox.Add(control,0,wx.EXPAND)
    ok_button = wx.Button(panel, wx.ID_OK)
    cancel_button = wx.Button(panel, wx.ID_CANCEL)
    button_sizer = wx.StdDialogButtonSizer()
    button_sizer.AddButton(ok_button)
    button_sizer.AddButton(cancel_button)
    button_sizer.Realize()
    if button_sizer:
        mainvbox.Add(button_sizer,0,wx.ALIGN_RIGHT|wx.TOP,15)
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
            if not filename.startswith("__"):
                impfile, imppath, impdescription = imp.find_module(filename.split(".")[0],[directory])
                module = imp.load_module("{}_plugin".format(filename.split(".")[0]), 
                                         impfile, imppath, impdescription)
                
                if module.plugin_name not in plugins.setdefault(module.plugin_type, {}):
                    plugins[module.plugin_type][module.plugin_name] = module.Backend
        except Exception as e:
            logging.warning(e)
        finally:
            try:
                impfile.close()
            except:
                pass 
    return plugins
