import wx
import os
import signal
import xml.etree.ElementTree as ET
import multiprocessing
import argparse
import tempfile
import datetime
import time
import base64
import functools
import sys

import logging

sys.path.append(os.path.dirname(__file__))

import clippacloud
from clippacloud import exceptions
from clippacloud import clipcatcher
from clippacloud import config
from clippacloud import plugin

import icon
import traceback
from clippacloud import clipboard

backend = None

class Settings(object):
    def __init__(self, backend, connectiondata):
        self._backend = backend
        self._connectiondata = connectiondata
        self.xml = ET.Element("Settings")
        self.backend = backend
        self.connectiondata = connectiondata
        pass

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
        return cls(backend,connectiondata)

projectname = "clippacloud"
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
logfilepath = os.path.join(settingsdirectory,"clippacloud.log")
logging.basicConfig(format=FORMAT,filename=logfilepath)
logging.info("Started clippacloud")

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

        #sizer = wx.FlexGridSizer(2, 2, 5, 5)
        #sizer.AddGrowableCol(1)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(backendlabel,0,wx.ALIGN_CENTER_VERTICAL|wx.RIGHT,5)
        sizer.Add(backend_combo,1, flag=wx.EXPAND)
        # box = wx.BoxSizer()

        mainvbox.Add(sizer,0,wx.EXPAND|wx.BOTTOM,15)

        # box.Add(ok_button, flag=wx.ALIGN_RIGHT)
        # box.Add(cancel_button, flag=wx.ALIGN_RIGHT)

        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        

        #sizer.Add(wx.BoxSizer())
        #sizer.Add(box,flag=wx.ALIGN_RIGHT)

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
            #self.DestroyChildren()
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

paused = False

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.AppendItem(item)
    return item

class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, top_window):
        # If we are using the development branch on Mac OSX, we can make it a menu bar item
        self.top_window = top_window
        # Cache
        icon.getTrayIconPausedIcon()
        if sys.platform == "darwin":
            try:
                super(TaskBarIcon, self).__init__(wx.TBI_CUSTOM_STATUSITEM)
                self.SetIcon(icon.getTrayIconIcon(),"Clippacloud")
            except (AttributeError,wx._core.PyAssertionError):
                super(TaskBarIcon, self).__init__(wx.TBI_DOCK)
                self.SetIcon(icon.getTrayIconIcon(),"Clippacloud")
        else:
            super(TaskBarIcon, self).__init__()
            self.SetIcon(icon.getTrayIconIcon(),"Clippacloud")


    def CreatePopupMenu(self):
        global paused
        menu = wx.Menu()
        if paused:
            label = "Resume Clippacloud"
        else:
            label = "Pause Clippacloud"
        create_menu_item(menu, label, self.on_pause)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit Clippacloud', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.IconFromBitmap(wx.Bitmap(path))
        self.SetIcon(icon, "Clippacloud")

    def on_pause(self, event):
        global paused
        paused = not paused
        if paused:
            self.SetIcon(icon.getTrayIconPausedIcon(),"Clippacloud")
        else:
            self.SetIcon(icon.getTrayIconIcon(),"Clippacloud")
        


    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.top_window.Destroy()

def make_backend(settings, app):
    initwindow = InitBackendWindow(settings, clippacloud.backends, app)
    initwindow.Show(True)
    app.SetTopWindow(initwindow)
    app.MainLoop()
    backend = globals()["backend"]
    return backend

def main():
    global backend
    parser = argparse.ArgumentParser(description='Cloud based clipboard syncing.')
    parser.add_argument('-c, --config', dest="config", type=str, nargs='?',
                       help='config file for clippacloud')
    args = parser.parse_args()
    clippacloud.init(args)
    app = wx.App()
    app.SetTopWindow(None)
    # wx is a dummy dummy
    frame = wx.Frame(None)
    app.SetTopWindow(frame)
    icon = TaskBarIcon(frame)
    settings = Settings.from_xml(settingstext)
    while True:
        if not settings.backend:
            backend = make_backend(settings,app)
            if backend is None:
                return 0
            settings.backend = backend.name
            settings.connectiondata = ET.Element("ConnectionData",backend.get_connection_data())
            break
        else:
            try:
                backend = clippacloud.backends[settings.backend]()
                backend.resume(settings.connectiondata)
                break
            except Exception as e:
                settings.backend = None
    clippacloud.backend = backend
    global modified
    modified = datetime.datetime.min
    def idle_func():
        global modified
        global paused
        global backend
        try:
            if not paused:
                cp = clipboard.Clipboard()
                clipcatcher.try_catch_clip(cp,backend)
                files = sorted(clippacloud.backend.list_files(), key=lambda x: x.modified)
                if files:
                    filedesc = files[-1]
                    if filedesc.modified > modified:
                        clippacloud.actions.set_clipboard_from_cloud(cp)
                        modified = filedesc.modified
                    cp.flush()
                    totalsize = sum(x.size for x in files)
                    while totalsize > config.max_size:
                        try:
                            clippacloud.backend.remove_file(files[0].path)
                        except:
                            pass
                        files = files[1:]
                        totalsize = sum(x.size for x in files)
        except exceptions.AccessRevokedException:
            dialog = wx.MessageDialog(None,"Clippacloud's access for your backend has been revoked.\nWould you like to reauthenticate?",
                                            "Access revoked",wx.YES_NO|wx.ICON_ERROR)
            response = dialog.ShowModal()
            if response != wx.ID_YES:
                app.Exit()
                return
            backend = None
            backend = make_backend(settings,app)
            clippacloud.backend = backend
            if backend is None:
                app.Exit()
                return
            settings.backend = backend.name
            settings.connectiondata = ET.Element("ConnectionData",backend.get_connection_data())

        except Exception as e:
            logging.error(traceback.format_exc())
        wx.CallLater(1000,idle_func)
    
    wx.CallLater(1000,idle_func)
    app.MainLoop()
    try:
        icon.Destroy()
    except:
        pass
    with open(settingsfilepath,"w") as outfile:
        outfile.write(ET.tostring(settings.to_xml()))
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
    except Exception as e:
        exit_code = 1
        logging.error(traceback.format_exc())
    logging.info("Closing clippacloud")
    logging.shutdown()
    exit(exit_code)