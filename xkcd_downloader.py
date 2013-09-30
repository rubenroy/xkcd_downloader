import requests
import os
import json
import threading
import Queue

max_threads = 70
folder = "xkcd_downloaded"
download_path = os.getenv("HOME")+"/"+folder

print_lock = threading.Lock()
q = Queue.Queue()


class Download(threading.Thread):
    page_url = ""

    def download(self):
        self.page_url = q.get()
        page_dict = json.loads(requests.get(self.page_url).text)
        image_url = page_dict["img"]
        filename = image_url.split("/")[-1]
        i = page_dict["num"]
        img_path = download_path + "/" + str(i) + ". " + filename
        t_path = img_path + ".txt"
        url = image_url
        response = requests.head(image_url)
        if response.status_code == 301:
            url = response.headers["location"]
            response = requests.get(url, allow_redirects=False)
            url = response.headers["location"]
            response = requests.head(url)
            image_url = url
        remote_size = int(response.headers["content-length"])
        try:
            local_size = int(os.path.getsize(img_path))
        except OSError:
            local_size = 0
        if remote_size != local_size:
            r = requests.get(response.url, stream=True)
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

    def __init__(self):
        super(Download, self).__init__()

    def run(self):
        while q.qsize() > 0:
            self.download()
            q.task_done()


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
    global max_threads
    url = "http://xkcd.org/info.0.json"
    latest = json.loads(requests.get(url).text)["num"]
    print 'Latest comic number is', latest
    range_input = raw_input('Enter comics to download'
                            '(eg: "55,630,666-999,1024"): ')
    if range_input.isspace() or not range_input:
        range_list = range(1, 404) + range(405, latest+1)
    else:
        range_list = get_range(range_input, latest)
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    for i in range_list:
        q.put("http://xkcd.com/"+str(i)+"/info.0.json")
    max_threads = min(len(range_list), max_threads)
    for i in range(max_threads):
        t = Download()
        t.daemon = True
        t.start()
    q.join()
if __name__ == '__main__':
    main()
