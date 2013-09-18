import requests,os
from bs4 import BeautifulSoup
def download(page_url,folder):
    print 'Opening ',page_url,'...'
    soup = BeautifulSoup(requests.get(page_url).text)
    tag = soup.find(id="comic").img
    image_url = tag["src"]
    filename = image_url.split('/')[-1]    
    f=open(os.getcwd()+"/"+folder+"/"+filename+".txt",'w')
    f.write(tag["title"])
    f.close()
    r = requests.get(image_url, stream = True)
    with open(os.getcwd()+"/"+folder+"/"+filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)
                f.flush()
def get_range(s,latest):
    r = []
    for i in s.split(","):
        if "-" in i:
            l = i.split("-")
            a,b = int(l[0]),int(l[1])
            if a > latest:
                break
            elif b > latest:
                b = latest
            r += range(a,b+1)
        elif int(i) > latest:
            r.append(int(i))
    return r
folder = "xkcd_downloaded"
soup = BeautifulSoup(requests.get("http://xkcd.com/").text)
tag = soup.find(attrs={"rel": "prev"})
latest = int(tag["href"].split("/")[1])+1
print 'Latest comic number is',latest
range_input=raw_input('\nEnter comics to download (eg: "55,630,666-999,1024"): ')
range_list=get_range(range_input,latest)
if not os.path.exists(folder):
    os.mkdir(folder)
for i in range_list:
    download("http://xkcd.com/"+str(i)+"/",folder)
