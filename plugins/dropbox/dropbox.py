from hoverboard import plugin, exceptions
import base64
import datetime
import sys
import os

old_path = sys.path
sys.path = sys.path+[os.path.dirname(__file__)]
import dropboxlib
from dropboxlib import client, rest, session
sys.path = old_path

class Backend(object):
    name = "Dropbox"
    _APP_SECRET_ENCODE = "dHEyZnJjcHoydGczeHl5|NWszZ3d1NzdxbndxMXdl"
    # Herp derp, they'll never figure it out
    _APP_KEY = base64.b64decode(_APP_SECRET_ENCODE.split("|")[0])
    _APP_SECRET = base64.b64decode(_APP_SECRET_ENCODE.split("|")[1])

    _ACCESS_TYPE = 'app_folder'

    def __init__(self):
        self.client = None
        self.access_token = None
        self.delta = None
        self.files = {}

    def resume(self, init_data, device_name):
        key = init_data.get("key")
        secret = init_data.get("secret")
        sess = session.DropboxSession(self._APP_KEY,self._APP_SECRET, self._ACCESS_TYPE )
        sess.set_token(key,secret)
        self.client = client.DropboxClient(sess)
        self.checkin(device_name)
        assert self.check_validity()

        self._make_dir("devices",True)
        self._make_dir("global",True)
        self._make_dir("device_dirs",True)
        self._make_dir("device_dirs/{}".format(device_name),True)

    def create_new(self,device_name):
        sess = session.DropboxSession(self._APP_KEY, self._APP_SECRET, self._ACCESS_TYPE)

        request_token = sess.obtain_request_token()
        url = sess.build_authorize_url(request_token)

        window_definition = {"title":"Authorize the app",
                             "controls":[{"type":plugin.LINK_CONTROL,
                                          "url":url,
                                          "text":"Follow this link to activate the app"}]}

        urlwindow = plugin.make_dialog(window_definition)
        response = urlwindow.run()
        urlwindow.destroy()
        self.access_token = None
        if response == plugin.RESPONSE_OK:
            self.access_token = sess.obtain_access_token(request_token)
            self.client = client.DropboxClient(sess)
        if not self.access_token:
            raise exceptions.FailedToCreateBackend
        self.checkin(device_name)
        self._make_dir("devices",True)
        self._make_dir("global",True)
        self._make_dir("device_dirs",True)
        self._make_dir("device_dirs/{}".format(device_name),True)

    def _make_dir(self,dirpath,ignore_dup=False):
        try:
            self.client.file_create_folder(dirpath)
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 403 and ignore_dup:
                pass
            else:
                raise e

    def _save_file(self,filepath,outpath=None):
        try:
            if outpath is None:
                outpath = os.path.basename(filepath)
            with open(filepath,"rb") as f:
                self.client.put_file(outpath,f,overwrite=True)
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def _save_data(self,data,outpath):
        try:
            self.client.put_file(outpath,data,overwrite=True)
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def push_clip(self,data,format="txt",device=None):
        now = datetime.datetime.utcnow()
        filename = str(now)
        if device is not None:
            path = "/device_dirs/{}/{}.{}".format(device,filename,format)
        else:
            path = "/global/{}.{}".format(filename,format)
        self._save_data(data,path)

    def remove_clip(self,filedata):
        try:
            self.client.file_delete(filedata.path)
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def _get_file(self,filename,path):
        try:
            hfile = self.client.get_file(filename)
            data = hfile.read()
            os.path.join(path,filename).write(data)
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def _get_file_data(self,filename):
        try:
            hfile = self.client.get_file(filename)
            data = hfile.read()
            return data
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def pull_clip(self,filedata):
        return self._get_file_data(filedata.path)

    def _refresh_files(self):
        has_more = True
        while has_more:
            delta = self.client.delta(self.delta)
            entries, reset, self.delta, has_more = delta["entries"], delta["reset"], delta["cursor"], delta["has_more"]
            for path,filedata in entries:
                if filedata is None:
                    try:
                        del(self.files[path])
                    except:
                        pass
                else:
                    self.files[path] = plugin.FileDescription(filedata["path"],datetime.datetime.strptime(filedata["modified"], "%a, %d %b %Y %H:%M:%S +0000"),filedata["bytes"],filedata["is_dir"])

    def list_clips(self,device_name=None):
        try:
            self._refresh_files()
            if device_name is None:
                return [x for x in self.files.values() if x.path.startswith("/global/")]
            else:
                return [x for x in self.files.values() if x.path.startswith("/device_dirs/{}/".format(device_name))]
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def _list_dirs(self):
        self._refresh_files()
        return [x for x in self.files.values() if x.is_dir]

    def get_connection_data(self):
        try:
            data = {"key":self.access_token.key,"secret":self.access_token.secret}
            return data
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def _get_latest_file(self,path):
        try:
            filename = sorted(self.list_files(), key=lambda x: x.modified, reverse=True)[0].path
            return self.get_file(filename,path)
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def _get_latest_file_data(self):
        try:
            filename = sorted(self.list_files(), key=lambda x: x.modified, reverse=True)[0].path
            return self.get_file_data(filename)
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def check_validity(self):
        try:
            self.client.account_info()
            return True
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                return False

    def get_devices(self,device_name):
        self._refresh_files()
        return [plugin.Device(x.path.split("/")[-1],x.modified) for x in sorted(self.files.values(),key=lambda x: x.modified,reverse=True) if x.path.startswith("/devices/") and x.path.split("/")[-1] != device_name]
        #devices = [plugin.Device(x.path.split("/")[-1], x.modified) for x in device_files ]
        #return list(devices)

    def checkin(self,device_name):
        self._save_data("{}".format(datetime.datetime.utcnow()),"devices/{}".format(device_name))

