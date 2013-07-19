import dropbox
from dropbox import client, rest, session
from clippacloud import plugin
import base64
import time
import datetime

plugin_name = "Dropbox"
plugin_type = plugin.BACKEND_PLUGIN

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

    def resume(self, init_data):
        key = init_data.get("key")
        secret = init_data.get("secret")
        sess = session.DropboxSession(self._APP_KEY,self._APP_SECRET, self._ACCESS_TYPE )
        sess.set_token(key,secret)
        self.client = client.DropboxClient(sess)
        assert self.check_validity()

    def create_new(self):
        sess = session.DropboxSession(self._APP_KEY, self._APP_SECRET, self._ACCESS_TYPE)

        request_token = sess.obtain_request_token()
        url = sess.build_authorize_url(request_token)

        window_definition = {"title":"Authorize the app",
                             "controls":[{"type":plugin.LINK_CONTROL,
                                          "url":url,
                                          "text":"Follow this link to activate the app"}]}

        urlwindow = plugin.make_dialog(window_definition)
        #urlwindow.set_transient_for(self)
        response = urlwindow.run()
        urlwindow.destroy()
        self.access_token = None
        if response == plugin.RESPONSE_OK:
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
                files.append(plugin.FileDescription(filedata["path"],datetime.datetime.strptime(filedata["modified"], "%a, %d %b %Y %H:%M:%S +0000"),filedata["bytes"]))
        return files

    def get_connection_data(self):
        data = {"key":self.access_token.key,"secret":self.access_token.secret}
        return data

    def get_latest_file(self,path):
        filename = sorted(self.list_files(), key=lambda x: x.modified, reverse=True)[0].path
        return self.get_file(filename,path)

    def get_latest_file_data(self):
        filename = sorted(self.list_files(), key=lambda x: x.modified, reverse=True)[0].path
        return self.get_file_data(filename)

    def check_validity(self):
        try:
            self.client.account_info()
            return True
        except:
            return False