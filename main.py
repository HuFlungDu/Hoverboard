#from gi.repository import Gtk, Gdk, GObject
#import gtk
#import gobject
import wx
import dropbox
from dropbox import client, rest, session
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


import clippacloud
from clippacloud import exceptions
from clippacloud import clipcatcher
from clippacloud import config

backend = None

class FileDescription(object):
    def __init__(self,path,modified,size):
        self.path = path
        self.modified = modified
        self.size = size
        pass

class Backend(object):
    pass

    #def connect(self):
    #    raise NotImplementedError

class MainApp(wx.App):
    def OnInit(self):
        self.keepGoing = True
        return True

    def main_quit(self):
        self.keepGoing = False

    def MainLoop(self):
        evtloop = wx.EventLoop()
        old = wx.EventLoop.GetActive()
        wx.EventLoop.SetActive(evtloop)
        while self.keepGoing:
            while evtloop.Pending():
                evtloop.Dispatch()
            time.sleep(0.10)
            #evtloop.ProcessIdle()

        wx.EventLoop.SetActive(old)
        self.keepGoing = True

class DropboxUrlWindow(wx.Dialog):
    def __init__(self,url,session, token):
        wx.Dialog.__init__(self,None,-1,"Authorize the app")
        panel = wx.Panel(self, -1)
        link = wx.HyperlinkCtrl(panel,-1,"Follow this link to activate the app",url)
        mainvbox = wx.BoxSizer(wx.VERTICAL)
        mainvbox.Add(link)
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
        self.Fit()


class DropboxBackend(Backend):
    name = "Dropbox"
    _APP_SECRET_ENCODE = "dHEyZnJjcHoydGczeHl5|NWszZ3d1NzdxbndxMXdl"
    # Herp derp, they'll never figure it out
    _APP_KEY = base64.b64decode(_APP_SECRET_ENCODE.split("|")[0])
    _APP_SECRET = base64.b64decode(_APP_SECRET_ENCODE.split("|")[1])

    _ACCESS_TYPE = 'app_folder'

    def __init__(self):        
        self.client = None
        self.access_token = None

    def resume(self, init_data):
        key = init_data.get("key")
        secret = init_data.get("secret")
        sess = session.DropboxSession(self._APP_KEY,self._APP_SECRET, self._ACCESS_TYPE )
        sess.set_token(key,secret)
        self.client = client.DropboxClient(sess)


    def create_new(self):
        sess = session.DropboxSession(self._APP_KEY, self._APP_SECRET, self._ACCESS_TYPE)

        request_token = sess.obtain_request_token()
        url = sess.build_authorize_url(request_token)

        urlwindow = DropboxUrlWindow(url,sess,request_token)
        #urlwindow.set_transient_for(self)
        response = urlwindow.ShowModal()
        urlwindow.Destroy()
        #response = urlwindow.run()
        self.access_token = None
        if response == wx.ID_OK:
            self.access_token = sess.obtain_access_token(request_token)
            self.client = client.DropboxClient(sess)

        #urlwindow.destroy()

        if not self.access_token:
            raise exceptions.FailedToCreateBackend

        # webbrowser.open_new_tab(url)
        # self.access_token = sess.obtain_access_token(request_token)

    def save_file(self,filepath,outpath=None):
        if outpath is None:
            outpath = os.path.basename(filepath)
        with open(filepath,"rb") as f:
            self.client.put_file(outpath,f)

    def save_data(self,data,outpath):
        #tmpfile, tmppath = tempfile.mkstemp()
        #with os.fdopen(tmpfile,"wb") as outfile:
        #    outfile.write(data)
        #with open(tmppath,"rb") as f:
        self.client.put_file(outpath,data)
        #os.remove(tmppath)

    def remove_file(self,filename):
        self.client.file_delete(filename)

    def get_file(self,filename,path):
        hfile = self.client.get_file(filename)
        data = hfile.read()
        os.path.join(path,filename).write(data)

    def get_file_data(self,filename):
        hfile = self.client.get_file(filename)
        data = hfile.read()
        return data

    def list_files(self):
        files = []
        metadata = self.client.metadata("/")
        contents = metadata["contents"]
        for filedata in contents:
            if not filedata["is_dir"]:
                files.append(FileDescription(filedata["path"],datetime.datetime.strptime(filedata["modified"], "%a, %d %b %Y %H:%M:%S +0000"),filedata["bytes"]))
        return files

    def get_connection_data(self):
        data = ET.Element("ConnectionData",{"key":self.access_token.key,"secret":self.access_token.secret})
        return data

    def get_latest_file(self,path):
        filename = sorted(self.list_files(), key=lambda x: x.modified, reverse=True)[0].path
        return self.get_file(filename,path)

    def get_latest_file_data(self):
        filename = sorted(self.list_files(), key=lambda x: x.modified, reverse=True)[0].path
        return self.get_file_data(filename)        


backends = [DropboxBackend]


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
    os.mkdir(settingsdirectory)
settingsfilepath = os.path.join(settingsdirectory,"settings.xml")
lockfilepath = os.path.join(settingsdirectory,".lock")
#Create the settings file, so the read below will work during first run
if not os.path.isfile(settingsfilepath):
    open(settingsfilepath,'w').close()
#Read the settings file
with open(settingsfilepath,'r') as settingsfile:
    settingstext = settingsfile.read()

# APP_KEY = 'tq2frcpz2tg3xyy'
# APP_SECRET = '5k3gwu77qnwq1we'

# ACCESS_TYPE = 'app_folder'
# sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)

# request_token = sess.obtain_request_token()
# url = sess.build_authorize_url(request_token)

# webbrowser.open_new_tab(url)
# access_token = sess.obtain_access_token(request_token)

class InitBackendWindow(wx.Frame):
    def __init__(self,settings, backends):
        wx.Frame.__init__(self,None,-1,"Initialize Backend")
        panel = wx.Panel(self, -1)

        backendlabel = wx.StaticText(panel, -1, "Choose backend:")
        backend_combo = wx.Choice(panel, -1, choices=[backend.name for backend in backends])

        backend_combo.SetStringSelection(backends[0].name)

        ok_button = wx.Button(panel, wx.ID_OK)
        ok_button.Bind(wx.EVT_BUTTON,functools.partial(self.on_ok_button_clicked,combo=backend_combo))
        cancel_button = wx.Button(panel, wx.ID_CANCEL)
        cancel_button.Bind(wx.EVT_BUTTON,self.on_cancel_button_clicked)

        sizer = wx.FlexGridSizer(2, 2, 5, 5)
        sizer.AddGrowableCol(1)
        sizer.Add(backendlabel,flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(backend_combo, flag=wx.EXPAND)
        box = wx.BoxSizer()

        box.Add(cancel_button, flag=wx.ALIGN_RIGHT)
        box.Add(ok_button, flag=wx.ALIGN_RIGHT)

        sizer.Add(wx.BoxSizer())
        sizer.Add(box,flag=wx.ALIGN_RIGHT)


        border = wx.BoxSizer()
        border.Add(sizer, 0, wx.ALL, 15)
        panel.SetSizerAndFit(border)
        self.Fit()

        #mainvbox = gtk.VBox()

        #self.maingrid = gtk.Grid()
        #backendhbox = gtk.HBox()
        #backendlabel = gtk.Label("Choose backend:")
        #maincombo = gtk.combo_box_new_text()
        #for backend in backends:
        #    maincombo.append_text(backend.name)
        #maincombo.set_active(0)
        #backendhbox.pack_start(backendlabel,False,True,0)
        #backendhbox.pack_start(maincombo,True,True,0)
        #buttonhbox = gtk.HBox()
        #okbutton = gtk.Button(stock = gtk.STOCK_OK)
        #cancelbutton = gtk.Button(stock = gtk.STOCK_CANCEL)
        #buttonhbox.pack_start(cancelbutton,True,False,0)
        #buttonhbox.pack_start(okbutton,False,False,0)
        #mainvbox.pack_start(backendhbox,False,False,0)
        #mainvbox.pack_start(buttonhbox,False,False,0)
        #self.maingrid.attach(backendlabel,0,0,1,1)
        #self.maingrid.attach(maincombo,1,0,2,1)
        #self.maingrid.attach(okbutton,2,1,1,1)
        #self.maingrid.attach(cancelbutton,1,1,1,1)
        #self.add(mainvbox)
        #okbutton.connect("clicked",self.on_okbutton_clicked,maincombo)
        #self.connect("delete-event", self.on_kill)
        #self.connect("destroy", self.on_kill)

    def on_ok_button_clicked(self,button,combo):
        
        text = combo.GetStringSelection()
        for backend in backends:
            if backend.name == text:
                break
        else:
            raise Exception
        #Eww
        globals()["backend"] = backend()
        self.Show(False)
        try:
            globals()["backend"].create_new()
            self.DestroyChildren()
            self.Destroy()



            #gtk.main_quit()
        except Exception as e:
            print e
            self.Show(True)

    def on_cancel_button_clicked(self,button):
        self.Destroy()

    def run(self,app):
        app.MainLoop()
        return globals()["backend"]

    def on_kill(self,*args):
        gtk.main_quit()
        pass

def on_kill(window, *args):
    gtk.main_quit()

def make_icon_popup(icon, button, time, paused):
    menu = gtk.Menu()
    quit = gtk.MenuItem()
    pause = gtk.MenuItem()
    if paused[0]:
        pause.set_label("Resume clippacloud")
    else:
        pause.set_label("Pause clippacloud")

    def pause_unpause_cloud(item,paused):
        paused[0] = not paused[0]

    pause.connect("activate",pause_unpause_cloud, paused)

    quit.set_label("Exit clippacloud")

    quit.connect("activate", gtk.main_quit)

    menu.append(pause)
    menu.append(quit)

    menu.show_all()

    menu.popup(None, None, gtk.status_icon_position_menu, button, time, icon) # previous working pygtk line

paused = False

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.AppendItem(item)
    return item

class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self):
        super(TaskBarIcon, self).__init__()
        self.set_icon("icon.png")
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

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

    def on_left_down(self, event):
        print 'Tray icon was left-clicked.'

    def on_pause(self, event):
        global paused
        paused = not paused
        


    def on_exit(self, event):
        wx.CallAfter(self.Destroy)

def main():
    # icon = gtk.status_icon_new_from_stock(gtk.STOCK_EDIT)
    # icon.set_title("ClippaCloud")
    # icon.set_visible(True)
    # paused = [False]
    # icon.connect("popup-menu",make_icon_popup, paused)
    parser = argparse.ArgumentParser(description='Tiling window manager.')
    parser.add_argument('-c, --config', dest="config", type=str, nargs='?',
                       help='config file for manager')
    args = parser.parse_args()
    clippacloud.init(args)
    app = wx.PySimpleApp()
    settings = Settings.from_xml(settingstext)
    if True or not settings.backend:
        initwindow = InitBackendWindow(settings, backends)
        initwindow.Show(True)
        app.SetTopWindow(initwindow)
        #backend = initwindow.run(app)
        app.MainLoop()
        backend = globals()["backend"]
        settings.backend = backend.name
        settings.connectiondata = backend.get_connection_data()
        #initwindow.connect("delete-event", on_kill)
        #initwindow.connect("destroy", on_kill)
    else:
        try:
            backend = filter(lambda x: x.name == settings.backend,backends)[0]()
            backend.resume(settings.connectiondata)
        except:
            initwindow = InitBackendWindow(settings, backends)
            initwindow.show_all()
            backend = initwindow.run()
            settings.backend = backend.name
            settings.connectiondata = backend.get_connection_data()
            #initwindow.connect("delete-event", on_kill)
            #initwindow.connect("destroy", on_kill)
    clippacloud.backend = backend
    global modified
    modified = datetime.datetime.min
    def idle_func():
        global modified
        global paused
        try:
            if not paused:
                cp = wx.Clipboard.Get()
                clipcatcher.try_catch_clip(cp,backend)
                files = sorted(clippacloud.backend.list_files(), key=lambda x: x.modified)
                if files:
                    filedesc = files[-1]
                    if filedesc.modified > modified:
                        clippacloud.actions.set_clipboard_from_cloud(cp)
                        modified = filedesc.modified
                    cp.Flush()
                    totalsize = sum(x.size for x in files)
                    while totalsize > config.max_size:
                        clippacloud.backend.remove_file(files[0].path)
                        files = files[1:]
                        totalsize = sum(x.size for x in files)
        except Exception as e:
            print e
        wx.CallLater(1000,idle_func)
    icon = TaskBarIcon()
    wx.CallLater(1000,idle_func)
    app.MainLoop()
    #gobject.timeout_add(1000,idle_func)
    # try:
    #     gtk.main()
    # except:
    #     pass
    with open(settingsfilepath,"w") as outfile:
        outfile.write(ET.tostring(settings.to_xml()))


if __name__ == '__main__':
    main()