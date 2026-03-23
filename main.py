import requests
import concurrent.futures
import re

# 1. 精选源列表（涵盖港台新闻、日本综艺、纪录片）
SOURCES = [
    "https://live.fanmingming.com/tv/m3u/ipv6.m3u",       # 优质 IPv6 源
    "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u", # 综合大流量源
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u", # 广东/港台 IPv4 增强
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv.m3u"   # 经典整理源
]

def check_url(info, url):
    """测速并识别 IP 类型"""
    is_ipv6 = "[" in url or "ipv6" in url.lower()
    try:
        # 3秒超时，确保筛选出真正流畅的源
        response = requests.head(url, timeout=3, allow_redirects=True)
        if response.status_code == 200:
            return {"info": info, "url": url, "is_ipv6": is_ipv6}
    except:
        pass
    return None

def fetch_and_process():
    # 读取关键词
    with open("favorites.txt", "r", encoding="utf-8") as f:
        favs = [l.strip() for l in f if l.strip()]
    
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
        except: continue

    # 步骤 B: 多线程并发测速
    ipv4_list = []
    mixed_list = []
    
    print(f"搜集到 {len(raw_candidates)} 个备选，开始测速分流...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(check_url, info, url) for info, url in raw_candidates]
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            if res:
                mixed_list.append(res)
                if not res["is_ipv6"]:
                    ipv4_list.append(res)

    # 步骤 C: 分别写入两个文件
    # 1. 混合版 (适用于 5G 或已开启 IPv6 的网络)
    with open("integrated_list.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in mixed_list:
            f.write(f"{item['info']}\n{item['url']}\n")

    # 2. 纯 IPv4 版 (适用于你目前的天翼网关 Wi-Fi 环境)
    with open("ipv4_only.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in ipv4_list:
            f.write(f"{item['info']}\n{item['url']}\n")
    
    print(f" 任务完成！IPv4版: {len(ipv4_list)}个, 混合版: {len(mixed_list)}个")

if __name__ == "__main__":
    fetch_process()
  

  

  
  
