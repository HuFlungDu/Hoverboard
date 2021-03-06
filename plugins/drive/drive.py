from hoverboard import plugin
from hoverboard import exceptions
import base64
import time
import datetime
import json
import threading
import sys
import os

old_path = sys.path
sys.path = sys.path+[os.path.dirname(__file__),os.path.join(os.path.dirname(__file__),"googledrive")]
import httplib2
from googledrive import oauth2client
from googledrive import apiclient
from googledrive.apiclient.discovery import build
from googledrive.oauth2client.client import OAuth2WebServerFlow
sys.path = old_path

import StringIO



class Backend(object):
    name = "Google Drive"

    _CLIENT_ID = '701115588883.apps.googleusercontent.com'
    _CLIENT_SECRET = '-xEtLYa8E7xR_gBcB86jX1am'
    _OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive.appdata'

    _REDIRECT_URI="urn:ietf:wg:oauth:2.0:oob"

    _format_mimetypes = {"txt":"text/plain",
                         "png":"image/png"}

    def __init__(self):
        self.drive_service = None
        self.credentials = None
        self._app_folder_dir = None
        self._devices_dir = None
        self._global_dir = None
        self._device_dirs_dir = None
        self._device_dir = None
        # Drive doesn't like you to do two things at once, so we're going to lock all the network operations
        self._lock = threading.Lock()

    def resume(self, init_data,device_name):
        json_data = init_data.get("json")
        self.credentials = oauth2client.client.Credentials.new_from_json(json_data)
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        self.drive_service = build('drive', 'v2', http=http)
        assert self.check_validity()
        self._identify_directories(device_name)
        self._make_initial_directories(device_name)

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
        self._make_initial_directories(device_name)

    def _identify_directories(self,device_name):
        try:
            with self._lock:
                appdata_folder = self.drive_service.files().get(fileId='appdata').execute()
            self._app_folder_dir = appdata_folder['id']
            with self._lock:
                files = self.drive_service.files().list(q="'{}' in parents and mimeType = 'application/vnd.google-apps.folder' and (title = 'devices' or title = 'global' or title = 'device_dirs')".format(self._app_folder_dir),fields="items(title,id)").execute()
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
                with self._lock:
                    files = self.drive_service.children().list(q="mimeType = 'application/vnd.google-apps.folder' and title = '{}'".format(device_name),folderId=self._device_dirs_dir).execute()
                if len(files["items"]):
                    self._device_dir = files["items"][0]["id"]
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ('rateLimitExceeded', 'userRateLimitExceeded'):
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e

    def _make_initial_directories(self,device_name):
        try:
            if self._devices_dir is None:
                with self._lock:
                    devices_dir = self.drive_service.files().insert(body={"title":"devices","parents":[{"id":self._app_folder_dir}], "mimeType":"application/vnd.google-apps.folder"}).execute()
                self._devices_dir = devices_dir["id"]
            if self._global_dir is None:
                with self._lock:
                    global_dir = self.drive_service.files().insert(body={"title":"global","parents":[{"id":self._app_folder_dir}], "mimeType":"application/vnd.google-apps.folder"}).execute()
                self._global_dir = global_dir["id"]
            if self._device_dirs_dir is None:
                with self._lock:
                    device_dirs_dir = self.drive_service.files().insert(body={"title":"device_dirs","parents":[{"id":self._app_folder_dir}], "mimeType":"application/vnd.google-apps.folder"}).execute()
                self._device_dirs_dir = device_dirs_dir["id"]
            if self._device_dir is None:
                with self._lock:
                    device_dir = self.drive_service.files().insert(body={"title":device_name,"parents":[{"id":self._device_dirs_dir}], "mimeType":"application/vnd.google-apps.folder"}).execute()
                self._device_dir = device_dir["id"]
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e

    def _save_data(self,data,filename,directory,mimetype):
        try:
            media_body = apiclient.http.MediaIoBaseUpload(fd=StringIO.StringIO(data), mimetype=mimetype, resumable=True)
            body = {'title': filename,
                    'mimeType': mimetype,
                    "parents": [{"id":directory}]}
            with self._lock:
                self.drive_service.files().insert(body=body,media_body=media_body).execute()
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e
        
    def _get_device_dir(self,device):
        try:
            with self._lock:
                files = self.drive_service.files().list(q="'{}' in parents and mimeType = 'application/vnd.google-apps.folder'".format(self._device_dirs_dir), fields="items(id,title)").execute()
                if len(files["items"]):
                    directory = next((x for x in files["items"] if x["title"] == device),None)
                if directory is not None:
                    directory = directory["id"]
                else:
                    # This shouldn't occur, but if it does we want to know about it
                    raise ValueError
            return directory
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e

    def push_clip(self,data,format="txt",device=None):
        if device is not None:
            directory = self._get_device_dir(device)
        else:
            directory = self._global_dir
        now = datetime.datetime.utcnow()
        filename = "{}.{}".format(str(now),format)
        mimetype = self._format_mimetypes[format]
        self._save_data(data,filename,directory,mimetype)

    def remove_clip(self,filedata):
        try:
            with self._lock:
                self.drive_service.files().delete(fileId=filedata.extra_data["id"]).execute()
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e

    def _get_file_data(self,download_url):
        resp, content = self.drive_service._http.request(download_url)
        if resp.status == 200:
            return content
        elif resp.status == 401:
            raise exceptions.AccessRevokedException()
        elif resp.status == 403:
            raise exceptions.ConnectivityException()
        else:
            raise ValueError

    def pull_clip(self,filedata):
        return self._get_file_data(filedata.extra_data["downloadUrl"])

    def list_clips(self,device_name=None,formats=None):
        try:
            directory = None
            if device_name is not None:
                directory = self._get_device_dir(device_name)
            else:
                directory = self._global_dir

            if formats is None:
                query = ""
            else:
                query = "and ({})".format(" or ".join("mimtetype = {}".format(self._format_mimetypes[x]) for x in formats))
            with self._lock:
                files = self.drive_service.files().list(q="'{}' in parents {}".format(directory,query),fields="items(modifiedDate,title,downloadUrl,fileSize,id)").execute()
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e
        return [plugin.FileDescription(x["title"],x["title"].split(".")[-1],datetime.datetime.strptime(x["modifiedDate"], "%Y-%m-%dT%H:%M:%S.%fZ"),int(x["fileSize"]),False,{"downloadUrl":x["downloadUrl"],"id":x["id"]}) for x in files["items"]]

    def get_connection_data(self):
        #Compared to dropbox, the drive API and accompanying docuementation is... Rudimentary.
        data = {"json":self.credentials.to_json()}
        return data

    def check_validity(self):
        try:
            with self._lock:
                self.drive_service.about().get().execute()
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e
        return True

    def get_devices(self,device_name):
        try:
            with self._lock:
                files = self.drive_service.files().list(q="'{}' in parents".format(self._devices_dir),fields="items(modifiedDate,title)").execute()
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e
        return [plugin.Device(x["title"],datetime.datetime.strptime(x["modifiedDate"], "%Y-%m-%dT%H:%M:%S.%fZ")) for x in files["items"] if x["title"] != device_name]

    def checkin(self,device_name):
        try:
            # This is a workaround since there is a bug with filtering on parent and title here.
            fileid = None
            with self._lock:
                files = self.drive_service.files().list(q="'{}' in parents".format(self._devices_dir,device_name),fields="items(title,id)").execute()
            if len(files["items"]):
                fileid = next((x for x in files["items"] if x["title"] == device_name),None)
            if fileid is not None:
                with self._lock:
                    self.drive_service.files().touch(fileId=fileid["id"]).execute()
            else:
                self._save_data("{}".format(datetime.datetime.utcnow()),device_name,self._devices_dir,"text/plain")
        except oauth2client.client.AccessTokenRefreshError:
            raise exceptions.AccessRevokedException()
        except apiclient.errors.HttpError as e:
            if e["code"] == 401:
                raise exceptions.AccessRevokedException()
            elif e["code"] == 403:
                if e['errors'][0]['reason'] in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    raise exceptions.ConnectivityException()
                else:
                    raise e
            else:
                raise e
