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
    # _APP_SECRET_ENCODE = "dHEyZnJjcHoydGczeHl5|NWszZ3d1NzdxbndxMXdl"
    # # Herp derp, they'll never figure it out
    # _APP_KEY = base64.b64decode(_APP_SECRET_ENCODE.split("|")[0])
    # _APP_SECRET = base64.b64decode(_APP_SECRET_ENCODE.split("|")[1])

    _CLIENT_ID = '701115588883.apps.googleusercontent.com'
    _CLIENT_SECRET = '-xEtLYa8E7xR_gBcB86jX1am'
    _OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

    # _ACCESS_TYPE = 'app_folder'
    _REDIRECT_URI="urn:ietf:wg:oauth:2.0:oob"

    def __init__(self):
        self.drive_service = None
        self.credentials = None

    def resume(self, init_data):
        json_data = init_data.get("json")
        self.credentials = oauth2client.client.Credentials.new_from_json(json_data)
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        self.drive_service = build('drive', 'v2', http=http)
        assert self.check_validity()

    def create_new(self):
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
                files.append(plugin.FileDescription(filedata["path"],datetime.datetime.strptime(filedata["modified"], "%a, %d %b %Y %H:%M:%S +0000"),filedata["bytes"]))
        return files

    def get_connection_data(self):
        #Compared to dropbox, the drive API and accompanying docuementation is... Rudimentary.
        data = {"json":self.credentials.to_json()}
        return data

    def get_latest_file(self,path):
        filename = sorted(self.list_files(), key=lambda x: x.modified, reverse=True)[0].path
        return self.get_file(filename,path)

    def get_latest_file_data(self):
        filename = sorted(self.list_files(), key=lambda x: x.modified, reverse=True)[0].path
        return self.get_file_data(filename)

    def check_validity(self):
        try:
            self.drive_service.about().get()
            return True
        except Exception as e:
            print e
            return False
