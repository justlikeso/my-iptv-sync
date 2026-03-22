import requests
import concurrent.futures

# 1. 强力源列表
SOURCES = [
    "https://live.fanmingming.com/tv/m3u/ipv6.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u"
]

# 2. 测速函数：检查链接是否真的能打开
def check_url(channel_info, url):
    try:
        # 模拟浏览器访问，设置 3 秒超时，只读头部信息（快）
        response = requests.head(url, timeout=3, allow_redirects=True)
        if response.status_code == 200:
            return (channel_info, url)
    except:
        pass
    return None

def get_favorites():
    with open("favorites.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def fetch_and_filter():
    favs = get_favorites()
    raw_channels = []
    
    # 步骤 A: 抓取并初步筛选关键词
    for source_url in SOURCES:
        try:
            print(f"正在抓取源: {source_url}")
            res = requests.get(source_url, timeout=10)
            lines = res.text.split('\n')
            for i in range(len(lines)):
                if "#EXTINF" in lines[i]:
                    for fav in favs:
                        if fav.lower() in lines[i].lower():
                            if i + 1 < len(lines) and lines[i+1].startswith("http"):
                                raw_channels.append((lines[i], lines[i+1].strip()))
                                break
        except:
            continue

    print(f"初步搜集到 {len(raw_channels)} 个备选频道，开始测速...")

    # 步骤 B: 多线程并发测速（大幅缩短等待时间）
    valid_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(check_url, info, url) for info, url in raw_channels]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                valid_list.append(result)

    # 步骤 C: 写入文件
    with open("my_list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for info, url in valid_list:
            f.write(f"{info}\n{url}\n")
    
    print(f" 筛选完毕！最终保留了 {len(valid_list)} 个有效频道。")

if __name__ == "__main__":
    fetch_and_filter()
  

  
  
