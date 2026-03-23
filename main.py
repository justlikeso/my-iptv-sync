import requests
import concurrent.futures

# 1. 换一批更硬核、针对大陆优化的 IPv4 港台源
SOURCES = [
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv.m3u",   # 资深维护源
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u", # 广东/港台增强
    "https://raw.githubusercontent.com/FongMi/TV/main/itv/iptv.m3u",    # 蜂蜜源（非常全）
    "https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u"     # 综合补位源
]

def check_url(info, url):
    """强化测速：不仅看响应，还要看数据流开头"""
    is_ipv6 = "[" in url or "ipv6" in url.lower()
    try:
        # 模拟真实播放器，请求数据流的前 1024 字节
        # 如果连 1KB 数据都传不回来，直接判定为假源
        with requests.get(url, timeout=3, stream=True, allow_redirects=True) as r:
            if r.status_code == 200:
                # 尝试读取一小块数据，确认服务器真的在吐数据
                next(r.iter_content(chunk_size=1024))
                return {"info": info, "url": url, "is_ipv6": is_ipv6}
    except:
        pass
    return None

def fetch_and_process():
    # 读取关键词
    with open("favorites.txt", "r", encoding="utf-8") as f:
        favs = [l.strip() for l in f if l.strip()]
    
    raw_candidates = []
    print(f"正在深度扫描港台及日本频道...")

    for s_url in SOURCES:
        try:
            r = requests.get(s_url, timeout=10)
            lines = r.text.split('\n')
            for i in range(len(lines)):
                if "#EXTINF" in lines[i]:
                    for f in favs:
                        if f.lower() in lines[i].lower():
                            if i + 1 < len(lines) and lines[i+1].startswith("http"):
                                raw_candidates.append((lines[i], lines[i+1].strip()))
                                break
        except: continue

    ipv4_list = []
    mixed_list = []
    
    # 增加并发量到 50，因为我们要真实读取数据流，速度会慢一点
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_url, info, url) for info, url in raw_candidates]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                mixed_list.append(res)
                if not res["is_ipv6"]:
                    ipv4_list.append(res)

    # 写入文件
    with open("integrated_list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in mixed_list:
            f.write(f"{item['info']}\n{item['url']}\n")

    with open("ipv4_only.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in ipv4_list:
            f.write(f"{item['info']}\n{item['url']}\n")
    
    print(f"筛选完毕！最终可用 IPv4: {len(ipv4_list)} 个，混合版: {len(mixed_list)} 个")

if __name__ == "__main__":
    fetch_and_process()

