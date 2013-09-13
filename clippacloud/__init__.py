import imp
from clippacloud import config
from clippacloud import plugin
from clippacloud import exceptions
from clippacloud import clipboard
import threading
import collections
import logging
import traceback
import time
import datetime

plugins = {}
backends = {}
backend = None
last_modified = datetime.datetime.min
access_revoked = False
pull_threads = []

class UploadThread(threading.Thread):
    def __init__(self,group,queue_lock,queue):
        threading.Thread.__init__(self,group=group, target=self.upload_thread_func, args=(queue_lock,queue))
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def upload_thread_func(self,lock, queue):
        import clippacloud
        counter = 0
        while True:
            counter += 1
            if self.stopped():
                break
            if len(queue):
                if clippacloud.backend is not None and clippacloud.backend.check_validity():
                    data, filename = queue.popleft()
                    try:
                        if len(data) < clippacloud.config.max_size:
                            backend.save_data(data,filename)
                    except exceptions.AccessRevokedException:
                        print "here"
                        clippacloud.access_revoked = True
                    except Exception as e:
                        logging.error(traceback.format_exc())
            time.sleep(.5)

class CleanupThread(threading.Thread):
    def __init__(self,group,backend_lock):
        threading.Thread.__init__(self,group=group, target=self.cleanup_thread_func, args=(backend_lock,))
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def cleanup_thread_func(self,lock):
        import clippacloud
        while True:
            if self.stopped():
                break
            if clippacloud.backend is not None and clippacloud.backend.check_validity():
                with lock:
                    try:
                        files = sorted(clippacloud.backend.list_files(), key=lambda x: x.modified)
                    except exceptions.AccessRevokedException:
                        clippacloud.access_revoked = True
                    except Exception as e:
                        logging.error(traceback.format_exc())
                if files and not clippacloud.access_revoked:
                    totalsize = sum(x.size for x in files)
                    while totalsize > config.max_size:
                        try:
                            clippacloud.backend.remove_file(files[0].path)
                        except:
                            pass
                        files = files[1:]
                        totalsize = sum(x.size for x in files)
            time.sleep(.5)

class PullClipThread(threading.Thread):
    def __init__(self,group,backend_lock,queue,retry=False):
        threading.Thread.__init__(self,group=group, target=self.pull_clip_thread_func, args=(backend_lock,queue,retry))
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def pull_clip_thread_func(self,lock,queue,retry):
        import clippacloud
        while True:
            if self.stopped():
                break
            try:
                assert clippacloud.backend is not None and clippacloud.backend.check_validity()
                #cp = clipboard.Clipboard()
                with lock:
                    files = sorted(clippacloud.backend.list_files(), key=lambda x: x.modified)
                if files:
                    filedesc = files[-1]
                    if filedesc.modified > clippacloud.last_modified:
                        #clippacloud.actions.set_clipboard_from_cloud(cp,filedesc.path)
                        path = filedesc.path
                        data = clippacloud.backend.get_file_data(path)
                        clippacloud.last_modified = filedesc.modified
                        queue.append((data,path))

                    #cp.flush()
            except Exception as e:
                if not retry:
                    break
                time.sleep(.5)
                continue
            break


class SharedQueue(collections.deque):
    def __init__(self,lock):
        self.lock = lock
        collections.deque.__init__(self)
        #self.arr = collections.deque()

    def append(self,item):
        with self.lock:
            collections.deque.append(self,item)

    def appendleft(self,item):
        with self.lock:
            collections.deque.appendleft(self,item)

    def pop(self):
        with self.lock:
            return collections.deque.pop(self)

    def popleft(self):
        with self.lock:
            return collections.deque.popleft(self)



def init(args,settings,plugins_dir):
    if args.config:
        userconfig = imp.load_source('userconfig', args.config)
        userconfig.init(settings.config)
    else:
        config.init(max_size=settings.max_size,auto_push=settings.auto_push,auto_pull=settings.auto_pull)
    globals()["plugins"] = plugin.get_plugins(plugins_dir)
    globals()["backends"] = plugins[plugin.BACKEND_PLUGIN]
    globals()["settings"] = settings
    up_queue_lock = threading.Lock()
    globals()["upload_list"] = SharedQueue(up_queue_lock)
    globals()["upload_thread"] = UploadThread(None,up_queue_lock,upload_list)
    upload_thread.start()

    down_queue_lock = threading.Lock()
    globals()["download_list"] = SharedQueue(down_queue_lock)

    globals()["backend_lock"] = threading.Lock()
    globals()["cleanup_thread"] = CleanupThread(None,backend_lock)
    cleanup_thread.start()