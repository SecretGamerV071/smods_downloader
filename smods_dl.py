import http.client
import os.path

import threading
from re import search
from urllib import request, parse

BASE_URL = "https://catalogue.smods.ru/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36"
def download_mod(url, filename = None):
    if filename is None:
        filename = url[url.rfind("/")+1:]
    if os.path.exists(filename):
        print(f'Not downloading {url}, file already exists.')
        return
    n:http.client.HTTPResponse = request.urlopen(url)
    file_size = int(n.headers["Content-Length"])
    chunk_size = int(file_size / 100)

    print(f'Downloading {url} to {filename} ({(file_size / 1024):,.2f}Kb)')
    downloaded_bytes = 0
    with open(filename, 'wb') as file, request.urlopen(url) as resp:
        while True:
            chunk = resp.read(chunk_size)
            downloaded_bytes += len(chunk)
            if not chunk:
                break
            file.write(chunk)
            print(f'\r{(downloaded_bytes / 1024):,.2f}/{(file_size / 1024):,.2f} ({(downloaded_bytes/file_size * 100):.2f}%)', end="", flush=True)
    print("Done!")


def get_modsbase_download_url(game_id:str, mod_id:str) -> str:
    req_url = f"{BASE_URL}?s={mod_id}&app={game_id}"
    if game_id == "281990":
        req_url = f"https://stellaris.smods.ru/?s={mod_id}"
    if(game_id == "255710"):
        req_url = f"https://smods.ru/?s={mod_id}"
    if(game_id == "394360"):
        req_url = f"https://hearts-of-iron-4.smods.ru/?s={mod_id}"
    req = request.Request(req_url)
    req.add_header("User-Agent", USER_AGENT)
    resp = request.urlopen(req).read().decode()
    for line in resp.splitlines():
        if "skymods-excerpt-btn" in line:
            # print(line)
            temp = search("https://modsbase.com/(.*?)\"", line)
            if temp is None:
                continue
            modsbase_url = temp.group(0).strip('"')
            #print(modsbase_url)
            req_modsbase = request.Request(modsbase_url, method="POST")
            req_modsbase.add_header("User-Agent", USER_AGENT)
            req_modsbase.add_header("Content-Type", "application/x-www-form-urlencoded")
            mod_id = modsbase_url[modsbase_url.find("//")+2:]
            mod_id = mod_id[mod_id.find("/")+1:mod_id.rfind("/")]
            #print(mod_id)
            post_dict = {"op":"download2", "id" : mod_id, "referrer" : modsbase_url, "rand" : "", "method_free":"", "method_premium":""}
            post_data = parse.urlencode(post_dict).encode()
            #print(post_data)
            resp = request.urlopen(req_modsbase, data=post_data)
            resp_str:str = resp.read().decode()
            dl_url = None
            for line in resp_str.splitlines():
                if "cgi-bin" in line:
                    dl_match = search("https:.*?\"", line)
                    if dl_match is not None:
                        dl_url = dl_match.group().strip('"')
            return dl_url
    return None

def get_mod_ids_from_collection(collection_link):
    print(f"Getting modids from {collection_link}")
    resp = request.urlopen(collection_link).read().decode()
    result = []
    for line in resp.splitlines():
        if "sharedfile_" in line:
            line = line[line.find("file_")+5:]
            line = line[:line.find('"')]
            if line not in result:
                result.append(line)
    print(f"Got {len(result)} modids from collection.")
    return result

appid = None
with open("list.txt", "r") as modlist:
    appid = modlist.readline().strip('\n')
    mod_ids = list()
    for line in modlist.readlines():
        if line.startswith("!"):
            collection_modids = get_mod_ids_from_collection(line[1:])
            mod_ids.extend(collection_modids)
            continue
        id = line[line.rfind("id=")+3:].strip('\n')
        mod_ids.append(id)

print(f'Getting URLs for {len(mod_ids)} items.')

mod_urls = list()
lock = threading.Lock()
failed = list()
def get_modsbase_download_url_thread(game_id: str, mod_id: str):
    url = get_modsbase_download_url(game_id,mod_id)
    if url is None:
        lock.acquire()
        print(f'Failed to acquire link for appid {game_id} modid {mod_id}')
        failed.append(mod_id)
        lock.release()
        return
    lock.acquire()
    mod_urls.append(url)
    print(f"Got {url} ({len(mod_urls)} / {len(mod_ids)})")
    lock.release()

threads = list()

for i in mod_ids:
    x = threading.Thread(target=get_modsbase_download_url_thread, args=(appid, i,))
    threads.append(x)
    x.start()
for i, t in enumerate(threads):
    t.join()

print(f'Downloading {len(mod_urls)} mods.')
for i, mod in enumerate(mod_urls):
    download_mod(mod)
    print(f"Done {i+1}/{len(mod_urls)}")

print("All done!")
if len(failed):
    print("Failed to get links for following modids:")
    for item in failed:
        print(item)
