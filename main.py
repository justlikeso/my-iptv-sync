import requests
import concurrent.futures

# 1. 强力源列表（包含港台新闻、日本综艺、纪录片等）
SOURCES = [
    "https://live.fanmingming.com/tv/m3u/ipv6.m3u",       # 优质 IPv6 源
    "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u", # 综合大流量源
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u", # 港台 IPv4 增强
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv.m3u",   # 经典整理源
    "https://raw.githubusercontent.com/Meroser/IPTV/main/IPTV.m3u"    # 备用综合源
]

def check_url(info, url):
    """测速并识别 IP 类型"""
    # 简单的 IPv6 判定逻辑
    is_ipv6 = "[" in url or "ipv6" in url.lower()
    try:
        # 设置 3 秒超时，模拟真实连接
        response = requests.head(url, timeout=3, allow_redirects=True)
        if response.status_code == 200:
            return {"info": info, "url": url, "is_ipv6": is_ipv6}
    except:
        pass
    return None

def fetch_and_process():
    # 读取关键词
    try:
        with open("favorites.txt", "r", encoding="utf-8") as f:
            favs = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        favs = ["凤凰", "HBO", "纬来", "翡翠"] # 默认兜底词

    raw_candidates = []
    print(f"开始从 {len(SOURCES)} 个源抓取关键词: {favs}")

    # 步骤 A: 抓取与初步筛选
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
        except:
            continue

    # 步骤 B: 多线程并发测速与分流
    ipv4_list = []
    mixed_list = []
    
    print(f"搜集到 {len(raw_candidates)} 个候选地址，开始测速分流...")
    # 使用 30 个线程提高速度
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_url, info, url) for info, url in raw_candidates]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                mixed_list.append(res)
                if not res["is_ipv6"]:
                    ipv4_list.append(res)

    # 步骤 C: 写入文件
    # 1. 混合版 (integrated_list.m3u)
    with open("integrated_list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in mixed_list:
            f.write(f"{item['info']}\n{item['url']}\n")

    # 2. 纯 IPv4 版 (ipv4_only.m3u)
    with open("ipv4_only.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in ipv4_list:
            f.write(f"{item['info']}\n{item['url']}\n")
    
    print(f"任务完成！IPv4列表已更新 ({len(ipv4_list)}个频道), 混合列表已更新 ({len(mixed_list)}个频道)")

if __name__ == "__main__":
    fetch_and_process()
  

  

  

  
  
