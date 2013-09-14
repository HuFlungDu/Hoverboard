import wx
import os
import xml.etree.ElementTree as ET
import argparse
import functools
import sys
from collections import namedtuple

import logging

# Look here first
sys.path.insert(0,os.path.dirname(__file__))
import hoverboard
from hoverboard import exceptions
from hoverboard import clipcatcher
from hoverboard import clipboard

import icon
import traceback


backend = None

class Settings(object):
    def __init__(self, backend, connectiondata, max_size=None, auto_push=None, auto_pull=None):
        self._backend = backend
        self._connectiondata = connectiondata
        self.xml = ET.Element("Settings")
        self.max_size = self._max_size = 1024*1024 if max_size is None else max_size
        self.auto_push = self._auto_push = True if auto_push is None else auto_push
        self.auto_pull = self._auto_pull = True if auto_pull is None else auto_pull


        self.backend = backend
        self.connectiondata = connectiondata
        

    def to_xml(self):
        return self.xml

    @property
    def backend(self):
        return self._backend

    @backend.setter
    def backend(self, value):
        conn = self.xml.find("Connection")
        if conn is not None:
            conn.set("backend",value)
        else:
            conn = ET.Element("Connection",{"backend":str(value)})
            self.xml.append(conn)
        self._backend = value


    @property
    def connectiondata(self):
        return self._connectiondata

    @connectiondata.setter
    def connectiondata(self,value):
        conn = self.xml.find("Connection")
        if conn is None:
            conn = ET.Element("Connection")
            self.xml.append(conn)
        conndata = conn.find("ConnectionData")
        if conndata is not None:
            conn.remove(conndata)
        conn.append(value)

    @property
    def max_size(self):
        return self._max_size

    @max_size.setter
    def max_size(self,value):
        config = self.xml.find("Config")
        if config is None:
            config = ET.Element("Config")
            self.xml.append(config)
        config.set("max_size",str(value))
        self._max_size = value

    @property
    def auto_push(self):
        return self._auto_push

    @auto_push.setter
    def auto_push(self,value):
        config = self.xml.find("Config")
        if config is None:
            config = ET.Element("Config")
            self.xml.append(config)
        config.set("auto_push",str(value))
        self._auto_push = value

    @property
    def auto_pull(self):
        return self._auto_pull

    @auto_pull.setter
    def auto_pull(self,value):
        config = self.xml.find("Config")
        if config is None:
            config = ET.Element("Config")
            self.xml.append(config)
        config.set("auto_pull",str(value))
        self._auto_pull = value

    @property
    def config(self):
        config = self.xml.find("Config")
        attribs = config.items()
        config_tuple = namedtuple("config",[key for key, __ in attribs])
        out_tuple = config_tuple(**dict(attribs))
        return out_tuple

    @classmethod
    def from_xml(cls,settingstext):

        try:
            settingsxml = ET.XML(settingstext)
        except ET.ParseError:
            settingsxml = ET.Element("Settings")
        connectionxml = settingsxml.find("Connection")
        if connectionxml is not None:
            backend = connectionxml.get("backend")
            connectiondata = connectionxml.find("ConnectionData") #Later...
        else:
            backend = ""
            connectiondata = ET.Element("ConnectionData")
        max_size = None
        auto_pull = None
        auto_push = None
        configxml = settingsxml.find("Config")
        if configxml is not None:
            max_size = configxml.get("max_size",None)
            auto_push = configxml.get("auto_push",None)
            auto_pull = configxml.get("auto_pull",None)
            if max_size is not None:
                max_size = int(max_size)
            if auto_pull is not None:
                auto_pull = auto_pull == "True"
            if auto_push is not None:
                auto_push = auto_push == "True"
        return cls(backend,connectiondata,max_size,auto_push,auto_pull)

projectname = "hoverboard"
if os.name != "posix":
    from win32com.shell import shellcon, shell
    homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
else:
    homedir = os.path.join(os.path.expanduser("~"), ".config")
settingsdirectory = os.path.join(homedir,projectname)
if not os.path.isdir(settingsdirectory):
    os.makedirs(settingsdirectory)
settingsfilepath = os.path.join(settingsdirectory,"settings.xml")
#Create the settings file, so the read below will work during first run
if not os.path.isfile(settingsfilepath):
    open(settingsfilepath,'w').close()
#Read the settings file
with open(settingsfilepath,'r') as settingsfile:
    settingstext = settingsfile.read()

FORMAT = '%(asctime)-15s %(message)s'
logfilepath = os.path.join(settingsdirectory,"hoverboard.log")
logging.basicConfig(format=FORMAT,filename=logfilepath)
logging.info("Started hoverboard")

class InitBackendWindow(wx.Frame):
    def __init__(self,settings, backends,app):
        wx.Frame.__init__(self,None,-1,"Initialize Backend")
        self.Bind(wx.EVT_CLOSE,self.on_cancel_button_clicked)
        self.app = app
        panel = wx.Panel(self, -1)

        backendlabel = wx.StaticText(panel, -1, "Choose backend:")
        backend_combo = wx.Choice(panel, -1, choices=backends.keys())

        backend_combo.SetStringSelection(iter(backends).next())

        mainvbox = wx.BoxSizer(wx.VERTICAL)

        ok_button = wx.Button(panel, wx.ID_OK)
        ok_button.Bind(wx.EVT_BUTTON,functools.partial(self.on_ok_button_clicked,combo=backend_combo,backends=backends))
        cancel_button = wx.Button(panel, wx.ID_CANCEL)
        cancel_button.Bind(wx.EVT_BUTTON,self.on_cancel_button_clicked)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(backendlabel,0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT,5)
        sizer.Add(backend_combo,1, flag=wx.EXPAND)

        mainvbox.Add(sizer,0,wx.EXPAND|wx.BOTTOM,15)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()

        if button_sizer:
            mainvbox.Add(button_sizer,0,wx.EXPAND)

        border = wx.BoxSizer()
        border.Add(mainvbox, 1, wx.ALL|wx.EXPAND, 15)
        panel.SetSizerAndFit(border)
        self.Fit()

    def on_ok_button_clicked(self,button,combo,backends):
        try:
            text = combo.GetStringSelection()
            #Eww
            globals()["backend"] = backends[(backend for backend in backends if backend == text).next()]()
            self.Show(False)
        except StopIteration:
            raise ValueError("Backend not found")

        try:
            globals()["backend"].create_new()
            wx.CallAfter(self.Destroy)
            wx.CallAfter(self.app.Exit)
        except Exception as e:
            logging.error(traceback.format_exc())
            self.Show(True)

    def on_cancel_button_clicked(self,button):
        wx.CallAfter(self.Destroy)
        wx.CallAfter(self.app.Exit)

    def run(self,app):
        app.MainLoop()
        return globals()["backend"]

class SettingsWindow(object):
    def __init__(self, settings):
        self.settings = settings
        self.values = {}
        self.window = wx.Dialog(None,-1,"Hoverboard Settings")
        panel = wx.Panel(self.window, -1)
        mainvbox = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel,-1,"Max size to use (mb): ")
        spinner = wx.SpinCtrl(panel,-1,str(settings.max_size/(1024*1024)),min=1,max=1000)
        spinner.Bind(wx.EVT_SPINCTRL,functools.partial(self.on_spinner_change,spinner=spinner,property="max_size",multiplier=(1024*1024),integer=True))
        self.values["max_size"] = settings.max_size

        sizer.Add(label,0,wx.RIGHT|wx.wx.ALIGN_CENTER_VERTICAL,5)
        sizer.Add(spinner,1,wx.EXPAND,0)

        mainvbox.Add(sizer,0,wx.EXPAND|wx.BOTTOM,15)

        auto_push_box = wx.CheckBox(panel,-1,"Automatically push clipboard content to server")
        auto_push_box.SetValue(settings.auto_push)
        auto_push_box.Bind(wx.EVT_CHECKBOX,functools.partial(self.on_check_pressed,box=auto_push_box,property="auto_push"))
        self.values["auto_push"] = settings.auto_push
        mainvbox.Add(auto_push_box,0,wx.EXPAND|wx.BOTTOM,15)

        auto_pull_box = wx.CheckBox(panel,-1,"Automatically pull clipboard content from server")
        auto_pull_box.SetValue(settings.auto_pull)
        auto_pull_box.Bind(wx.EVT_CHECKBOX,functools.partial(self.on_check_pressed,box=auto_pull_box,property="auto_pull"))
        self.values["auto_pull"] = settings.auto_pull
        mainvbox.Add(auto_pull_box,0,wx.EXPAND|wx.BOTTOM,15)

        label = wx.StaticText(panel,-1,"*Note: These settings are likely ineffectual if you are using the -(-)c(onfig) option")

        mainvbox.Add(label,0,wx.EXPAND|wx.BOTTOM,15)

        ok_button = wx.Button(panel, wx.ID_OK)
        cancel_button = wx.Button(panel, wx.ID_CANCEL)

        
        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()

        if button_sizer:
            mainvbox.Add(button_sizer,0,wx.EXPAND)

        border = wx.BoxSizer()
        border.Add(mainvbox, 1, wx.ALL|wx.EXPAND, 15)
        panel.SetSizerAndFit(border)
        self.window.Fit()

    # Thin wrapper
    def __getattr__(self,name):
        return getattr(self.window,name)

    def on_check_pressed(self,event,box,property):
        self.values[property] = box.GetValue()

    def on_spinner_change(self,event,spinner,property,multiplier=1, integer=False):
        value = spinner.GetValue()
        value *= multiplier
        if integer:
            value = int(value)
        self.values[property] = value



paused = False

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.AppendItem(item)
    return item

class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, top_window, app, settings):
        # If we are using the development branch on Mac OSX, we can make it a menu bar item
        self.top_window = top_window
        self.settings = settings
        self.app = app
        # Cache
        icon.getTrayIconPausedIcon()
        if sys.platform == "darwin":
            try:
                super(TaskBarIcon, self).__init__(wx.TBI_CUSTOM_STATUSITEM)
                self.SetIcon(icon.getTrayIconIcon(),"Hoverboard")
            except (AttributeError,wx._core.PyAssertionError):
                super(TaskBarIcon, self).__init__(wx.TBI_DOCK)
                self.SetIcon(icon.getTrayIconIcon(),"Hoverboard")
        else:
            super(TaskBarIcon, self).__init__()
            self.SetIcon(icon.getTrayIconIcon(),"Hoverboard")


    def CreatePopupMenu(self):
        global paused
        menu = wx.Menu()
        if paused:
            label = "Resume Hoverboard"
        else:
            label = "Pause Hoverboard"
        create_menu_item(menu, "Settings", self.on_settings)
        create_menu_item(menu, label, self.on_pause)
        if not hoverboard.config.auto_push:
            create_menu_item(menu, "Push clipboard now", self.on_push)
        if not hoverboard.config.auto_pull:
            create_menu_item(menu, "Pull clipboard now", self.on_pull)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit Hoverboard', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.IconFromBitmap(wx.Bitmap(path))
        self.SetIcon(icon, "Hoverboard")

    def on_pause(self, event):
        global paused
        paused = not paused
        if paused:
            self.SetIcon(icon.getTrayIconPausedIcon(),"Hoverboard")
        else:
            self.SetIcon(icon.getTrayIconIcon(),"Hoverboard")

    def on_push(self,event):
        cp = clipboard.Clipboard()
        clip = clipcatcher.try_catch_clip(cp,backend)
        if clip is not None:
            data, filename = clip
            hoverboard.upload_list.append((data,filename))

    def on_pull(self,event):
        if not any([x.is_alive() for x in hoverboard.pull_threads]):
            pull_thread = hoverboard.PullClipThread(None,hoverboard.backend_lock,hoverboard.download_list,True)
            hoverboard.pull_threads.append(pull_thread)
            pull_thread.start()

    def on_settings(self,event):
        window = SettingsWindow(self.settings)
        result = window.ShowModal()
        window.Destroy()
        if result == wx.ID_OK:
            hoverboard.settings.max_size = hoverboard.config.max_size = window.values["max_size"]
            hoverboard.settings.auto_pull = hoverboard.config.auto_pull = window.values["auto_pull"]
            hoverboard.settings.auto_push = hoverboard.config.auto_push = window.values["auto_push"]       


    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        wx.CallAfter(self.app.Exit)
        self.top_window.Destroy()

def make_backend(settings, app):
    initwindow = InitBackendWindow(settings, hoverboard.backends, app)
    initwindow.Show(True)
    app.SetTopWindow(initwindow)
    app.MainLoop()
    backend = globals()["backend"]
    return backend

def main(argv=None):
    if argv is None:
        argv = sys.argv
    global backend
    parser = argparse.ArgumentParser(description='Cloud based clipboard syncing.')
    parser.add_argument('-c, --config', dest="config", type=str, nargs='?',
                       help='config file for hoverboard')
    args = parser.parse_args(args=argv[1:])
    settings = Settings.from_xml(settingstext)
    hoverboard.init(args,settings,os.path.join(os.path.dirname(__file__),"plugins"))
    app = wx.App()
    app.SetTopWindow(None)
    # wx is a dummy dummy
    frame = wx.Frame(None)
    app.SetTopWindow(frame)
    icon = TaskBarIcon(frame,app,settings)
    while True:
        if not hoverboard.settings.backend:
            backend = make_backend(settings,app)
            if backend is None:
                return 0
            hoverboard.settings.backend = backend.name
            hoverboard.settings.connectiondata = ET.Element("ConnectionData",backend.get_connection_data())
            break
        else:
            try:
                backend = hoverboard.backends[hoverboard.settings.backend]()
                backend.resume(hoverboard.settings.connectiondata)
                break
            except Exception as e:
                hoverboard.settings.backend = None
    hoverboard.backend = backend
    def idle_func():
        global paused
        global backend
        try:
            if not paused:
                files = None
                if hoverboard.config.auto_push:
                    cp = clipboard.Clipboard()
                    clip = clipcatcher.try_catch_clip(cp,backend)
                    if clip is not None:
                        data, filename = clip
                        hoverboard.upload_list.append((data,filename))
                if hoverboard.config.auto_pull:
                    if not any([x.is_alive() for x in hoverboard.pull_threads]):
                        pull_thread = hoverboard.PullClipThread(None,hoverboard.backend_lock,hoverboard.download_list,False)
                        hoverboard.pull_threads.append(pull_thread)
                        pull_thread.start()
        except exceptions.AccessRevokedException:
            dialog = wx.MessageDialog(None,"Hoverboard's access for your backend has been revoked.\nWould you like to reauthenticate?",
                                            "Access revoked",wx.YES_NO|wx.ICON_ERROR)
            response = dialog.ShowModal()
            if response != wx.ID_YES:
                app.Exit()
                return
            backend = None
            backend = make_backend(hoverboard.settings,app)
            hoverboard.backend = backend
            if backend is None:
                app.Exit()
                return
            hoverboard.settings.backend = backend.name
            hoverboard.settings.connectiondata = ET.Element("ConnectionData",backend.get_connection_data())

        except Exception as e:
            logging.error(traceback.format_exc())
        if len(hoverboard.download_list):
            if hoverboard.backend is not None and hoverboard.backend.check_validity():
                cp = clipboard.Clipboard()
                data, filename = hoverboard.download_list.popleft()
                try:
                    hoverboard.actions.set_clipboard_from_cloud(cp,data,filename)
                except exceptions.AccessRevokedException:
                    hoverboard.access_revoked = True
                except Exception as e:
                    logging.error(traceback.format_exc())
        if hoverboard.access_revoked:
            dialog = wx.MessageDialog(None,"Hoverboard's access for your backend has been revoked.\nWould you like to reauthenticate?",
                                            "Access revoked",wx.YES_NO|wx.ICON_ERROR)
            response = dialog.ShowModal()
            if response != wx.ID_YES:
                app.Exit()
                return
            backend = None
            backend = make_backend(hoverboard.settings,app)
            hoverboard.backend = backend
            if backend is None:
                app.Exit()
                return
            hoverboard.settings.backend = backend.name
            hoverboard.settings.connectiondata = ET.Element("ConnectionData",backend.get_connection_data())
            hoverboard.access_revoked = False
        hoverboard.pull_threads = filter(lambda x: x.is_alive(),hoverboard.pull_threads)
        wx.CallLater(1000,idle_func)
    
    wx.CallLater(1000,idle_func)
    app.MainLoop()
    try:
        icon.Destroy()
    except:
        pass
    with open(settingsfilepath,"w") as outfile:
        outfile.write(ET.tostring(hoverboard.settings.to_xml()))
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
    except Exception as e:
        exit_code = 1
        logging.error(traceback.format_exc())
    logging.info("Closing hoverboard")
    logging.shutdown()
    hoverboard.upload_thread.stop()
    hoverboard.cleanup_thread.stop()
    for pull_thread in hoverboard.pull_threads:
        pull_thread.stop()
    exit(exit_code)