import requests
import os
import json
import threading

max_threads = 70
folder = "xkcd_downloaded"
download_path = os.getenv("HOME")+"/"+folder

active_threads = 0
lock = threading.Lock()
print_lock = threading.Lock()
queue = Queue.Queue()


class Download(threading.Thread):
    page_url = ""

    def download(self):
        page_dict = json.loads(requests.get(self.page_url).text)
        image_url = page_dict["img"]
        filename = image_url.split("/")[-1]
        i = page_dict["num"]
        img_path = download_path + "/" + str(i) + ". " + filename
        t_path = img_path + ".txt"
        remote_size = int(requests.head(image_url).headers["content-length"])
        try:
            local_size = int(os.path.getsize(img_path))
        except OSError:
            local_size = 0
        if remote_size != local_size:
            r = requests.get(image_url, stream=True)
            with open(img_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        f.flush()
            print_lock.acquire()
            print "Downloaded", i
            print_lock.release()
        remote_size = len(page_dict["transcript"])
        try:
            local_size = int(os.path.getsize(t_path))
        except OSError:
            local_size = 0
        if remote_size != local_size:
            f = open(t_path, 'w')
            f.write(page_dict["transcript"].encode("UTF-8"))
            f.close()

    def __init__(self, page_url):
        super(Download, self).__init__()
        self.page_url = page_url

    def run(self):
        self.download()
        lock.acquire()
        global active_threads
        active_threads -= 1
        lock.release()


def get_range(s, latest):
    r = []
    for i in s.split(","):
        if "-" in i:
            l = i.split("-")
            a, b = int(l[0]), int(l[1])
            if a > latest:
                break
            elif b > latest:
                b = latest
            r += range(a, b+1)
        elif int(i) <= latest:
            r.append(int(i))
    if 404 in r:
        r.remove(404)
    if 0 in r:
        r.remove(0)
    return list(set(r))


def main():
    global active_threads
    url = "http://xkcd.org/info.0.json"
    latest = json.loads(requests.get(url).text)["num"]
    print 'Latest comic number is', latest
    range_input = raw_input('Enter comics to download'
                            '(eg: "55,630,666-999,1024"): ')
    range_list = get_range(range_input, latest)
    if not os.path.exists(folder):
        os.mkdir(folder)
    for i in range_list:
        while True:
            lock.acquire()
            if(active_threads < max_threads):
                active_threads += 1
                lock.release()
                break
            lock.release()
        Download("http://xkcd.com/"+str(i)+"/info.0.json").start()
if __name__ == '__main__':
    main()
