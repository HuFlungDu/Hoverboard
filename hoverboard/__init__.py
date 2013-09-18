import imp
from hoverboard import config
from hoverboard import plugin
from hoverboard import exceptions
from hoverboard import clipboard
from hoverboard import actions
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
last_modified_device = datetime.datetime.min
last_checkin = datetime.datetime.min
last_pulled = "global"
access_revoked = False
pull_threads = []
devices = []

class UploadThread(threading.Thread):
    def __init__(self,group,queue_lock,queue):
        threading.Thread.__init__(self,group=group, target=self.upload_thread_func, args=(queue_lock,queue))
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def upload_thread_func(self,lock, queue):
        import hoverboard
        counter = 0
        while True:
            counter += 1
            if self.stopped():
                break
            if len(queue):
                try:
                    if hoverboard.backend is not None and hoverboard.backend.check_validity():
                        data, filename, directory = queue.popleft()
                        if len(data) < hoverboard.config.max_size:
                            backend.save_data(data,"{}/{}".format(directory,filename))
                except exceptions.AccessRevokedException:
                    hoverboard.access_revoked = True
                except Exception as e:
                    logging.error(traceback.format_exc())
            time.sleep(.5)

class CleanupThread(threading.Thread):
    def __init__(self,group,backend_lock,device_name):
        threading.Thread.__init__(self,group=group, target=self.cleanup_thread_func, args=(backend_lock,))
        self._stop = threading.Event()
        self.device_name = device_name

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def cleanup_thread_func(self,lock):
        import hoverboard
        while True:
            if self.stopped():
                break
            try:
                # Not strictly cleanup, but I don't feel like starting up another thread.
                hoverboard.devices = hoverboard.backend.get_devices(self.device_name)
                timedelta = datetime.datetime.now() - last_checkin
                # Check in every tenish minutes
                if (timedelta.days * 86400 + timedelta.seconds)/60 > 10:
                    hoverboard.backend.checkin()
                    last_checkin = datetime.datetime.now()
                for directory in ("global",self.device_name):
                    if hoverboard.backend is not None and hoverboard.backend.check_validity() and directory:
                        with lock:
                            files = sorted(hoverboard.backend.list_files(directory), key=lambda x: x.modified)
                        if files and not hoverboard.access_revoked:
                            totalsize = sum(x.size for x in files)
                            while totalsize > config.max_size:
                                try:
                                    hoverboard.backend.remove_file(files[0].path)
                                except:
                                    pass
                                files = files[1:]
                                totalsize = sum(x.size for x in files)
            except exceptions.AccessRevokedException:
                hoverboard.access_revoked = True
            except Exception as e:
                logging.error(traceback.format_exc())
            time.sleep(.5)

class PullClipThread(threading.Thread):
    def __init__(self,group,backend_lock,queue,retry=False,directory="global"):
        threading.Thread.__init__(self,group=group, target=self.pull_clip_thread_func, args=(backend_lock,queue,retry,directory))
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def pull_clip_thread_func(self,lock,queue,retry,directory):
        import hoverboard
        while True:
            if self.stopped():
                break
            try:
                if directory == "global":
                    last_modified = hoverboard.last_modified
                else:
                    last_modified = hoverboard.last_modified_device
                assert hoverboard.backend is not None and hoverboard.backend.check_validity()
                with lock:
                    files = sorted(hoverboard.backend.list_files(directory), key=lambda x: x.modified)
                if files:
                    filedesc = files[-1]
                    if filedesc.modified > last_modified or (hoverboard.last_pulled != directory and retry):
                        path = filedesc.path
                        data = hoverboard.backend.get_file_data(path)
                        if directory == "global":
                            hoverboard.last_modified = filedesc.modified
                        else:
                            hoverboard.last_modified_device = filedesc.modified
                        hoverboard.last_pulled = directory
                        queue.append((data,path))

            except exceptions.AccessRevokedException:
                hoverboard.access_revoked = True
                if not retry:
                    break
                time.sleep(.5)
                continue
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
        config.init(max_size=settings.max_size,auto_push=settings.auto_push,auto_pull_global=settings.auto_pull_global,auto_pull_device=settings.auto_pull_device)
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
    globals()["cleanup_thread"] = CleanupThread(None,backend_lock,settings.device_name)
    cleanup_thread.start()
