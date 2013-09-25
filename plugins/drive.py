from hoverboard import plugin
import base64
import time
import datetime
import json

import httplib2

import oauth2client
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow

plugin_name = "Google Drive"
plugin_type = plugin.BACKEND_PLUGIN



class Backend(object):
    name = "Google Drive"

    _CLIENT_ID = '701115588883.apps.googleusercontent.com'
    _CLIENT_SECRET = '-xEtLYa8E7xR_gBcB86jX1am'
    _OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

    # _ACCESS_TYPE = 'app_folder'
    _REDIRECT_URI="urn:ietf:wg:oauth:2.0:oob"

    def __init__(self):
        self.drive_service = None
        self.credentials = None
        self._app_folder_dir = None
        self._devices_dir = None
        self._global_dir = None
        self._device_dirs_dir = None

    def resume(self, init_data):
        json_data = init_data.get("json")
        self.credentials = oauth2client.client.Credentials.new_from_json(json_data)
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        self.drive_service = build('drive', 'v2', http=http)
        assert self.check_validity()
        # self._devices_dir = self._make_dir("devices",self._hoverboard_dir)
        # self._global_dir = self._make_dir("global",self._hoverboard_dir)
        # self._device_dirs_dir = self._make_dir("device_dirs",self._hoverboard_dir)
        # self._make_dir("{}".format(device_name),self._device_dirs_dir)

    def create_new(self,device_name):
        flow = OAuth2WebServerFlow(self._CLIENT_ID, self._CLIENT_SECRET, self._OAUTH_SCOPE, self._REDIRECT_URI)

        url = flow.step1_get_authorize_url()

        window_definition = {"title":"Authorize the app",
                             "controls":[{"type":plugin.LINK_CONTROL,
                                          "url":url,
                                          "text":"Follow this link to activate the app",
                                          "name":"URL_link"},
                                          {"type":plugin.TEXTINPUT_CONTROL,
                                          "label":"Verification code",
                                          "name":"verification_code"}]}

        urlwindow = plugin.make_dialog(window_definition)
        #urlwindow.set_transient_for(self)
        response = urlwindow.run()
        urlwindow.destroy()
        values = urlwindow.get_controls_data()
        code = values["verification_code"]
        self.credentials = flow.step2_exchange(code)

        http = httplib2.Http()
        http = self.credentials.authorize(http)

        if response == plugin.RESPONSE_OK:
            self.drive_service = build('drive', 'v2', http=http)
        else:
            raise exceptions.FailedToCreateBackend

        if not self.drive_service:
            raise exceptions.FailedToCreateBackend

        self._identify_directories(device_name)

        # self._make_dir("hoverboard",True)
        # self._make_dir("hoverboard/devices",True)
        # self._make_dir("hoverboard/global",True)
        # self._make_dir("hoverboard/device_dirs",True)
        # self._make_dir("hoverboard/device_dirs/{}".format(device_name),True)

        
        # webbrowser.open_new_tab(url)
        # self.access_token = sess.obtain_access_token(request_token)

    def _identify_directories(self,device_name):
        files = self.drive_service.files().list(q="'appdata' in parents and mimeType = 'application/vnd.google-apps.folder' and (title = 'devices' or title = 'global' or title = 'device_dirs')").execute()
        devices = [__ for __ in files["items"] if __["title"] == "devices"]
        if len(devices):
            self._devices_dir = devices[0]["id"]
        globallist = [__ for __ in files["items"] if __["title"] == "global"]
        if len(globallist):
            self._global_dir = globallist[0]["id"]
        device_dirs = [__ for __ in files["items"] if __["title"] == "device_dirs"]
        if len(device_dirs):
            self._device_dirs_dir = device_dirs[0]["id"]
        if self._device_dirs_dir is not None:
            files = self.drive_service.children().list(q="'mimeType = 'application/vnd.google-apps.folder' and title = '{}'".format(device_name),folderId=self._device_dirs_dir).execute()
            if len(files["items"]):
                self._device_dirs_dir = files[0]["id"]

    def _make_dir(self,name,parent=None):
            body = {
                'title': name,

                'mimeType': "application/vnd.google-apps.folder"
            }
            if parent is not None:
                body["parents"] = [{"id":parent}]
            directory = self.drive_service.files().insert(body=body).execute()
            return directory["id"]
            #self.client.file_create_folder(dirpath)

    def _save_file(self,filepath,outpath=None):
        return None
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
            path = "hoverboard/device_dirs/{}/{}.{}".format(device,filename,format)
        else:
            path = "hoverboard/global/{}.{}".format(filename,format)
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
                return [x for x in self.files.values() if x.path.startswith("hoverboard/global/")]
            else:
                return [x for x in self.files.values() if x.path.startswith("hoverboard/device_dirs/{}/".format(device_name))]
        except dropboxlib.rest.ErrorResponse as e:
            if e.status == 401:
                raise exceptions.AccessRevokedException()
            else:
                raise e

    def _list_dirs(self):
        self._refresh_files()
        return [x for x in self.files.values() if x.is_dir]

    def get_connection_data(self):
        #Compared to dropbox, the drive API and accompanying docuementation is... Rudimentary.
        data = {"json":self.credentials.to_json()}
        return data

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
        return [plugin.Device(x.path.split("/")[-1],x.modified) for x in self.files.values() if x.path.startswith("hoverboard/devices/") and x.path.split("/")[-1] != device_name]

    def checkin(self,device_name):
        self._save_data("{}".format(datetime.datetime.utcnow()),"hoverboard/devices/{}".format(device_name))
