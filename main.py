import requests
import concurrent.futures

# 1. 广撒网：汇集全网最强的 20+ 个聚合源
SOURCES = [
    "https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u",
    "https://raw.githubusercontent.com/ssili126/tv/main/itvlist.m3u",
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u",
    "https://raw.githubusercontent.com/FanMingming/live/main/tv/m3u/ipv6.m3u",
    "https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u",
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv.m3u",
    "https://raw.githubusercontent.com/Meroser/IPTV/main/IPTV.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "https://raw.githubusercontent.com/FongMi/TV/main/itv/iptv.m3u",
    "https://raw.githubusercontent.com/suppress-on/IPTV/main/live.m3u",
    "https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u",
    "https://raw.githubusercontent.com/K-S-V/IPTV/master/IPTV.m3u",
    "https://raw.githubusercontent.com/Memory-of-Life/IPTV/main/Live.m3u"
]

def clean_url(url):
    return url.split('$')[0].split(' ')[0].strip()

def check_url(info, url):
    url = clean_url(url)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        # 为了提高效率，这里只做基础连接测试，因为有的台在境外，深度测试太慢
        response = requests.head(url, timeout=2, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            return {"info": info, "url": url}
    except:
        pass
    return None

def fetch_and_process():
    # 增加更多关键词，特别是针对日本台和纪录片
    keyword_map = {
        "凤凰": ["凤凰", "Phoenix"],
        "HBO": ["HBO"],
        "Discovery": ["Discovery", "探索", "探險"],
        "国家地理": ["National", "地理", "Nat Geo"],
        "纬来": ["纬来", "Videoland"],
        "国兴": ["国兴", "Kokusai"],
        "翡翠": ["翡翠", "TVB"],
        "NHK": ["NHK", "日本"],
        "动物": ["Animal", "动物星球"],
        "历史": ["History", "历史频道"]
    }

    results = {}
    raw_candidates = []

    print("正在从全网 20+ 个源搜集频道，这可能需要一点时间...")

    for s_url in SOURCES:
        try:
            r = requests.get(s_url, timeout=15)
            lines = r.text.split('\n')
            for i in range(len(lines)):
                if "#EXTINF" in lines[i]:
                    name_line = lines[i]
                    for k, aliases in keyword_map.items():
                        if any(a.lower() in name_line.lower() for a in aliases):
                            if i + 1 < len(lines) and lines[i+1].startswith("http"):
                                raw_candidates.append((name_line, lines[i+1].strip(), k))
                                break
        except: continue

    print(f"搜集到 {len(raw_candidates)} 个候选链接，开始多线程筛选...")

    # 提高线程到 100，疯狂筛选
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(check_url, info, url) for info, url, k in raw_candidates]
        for i, f in enumerate(concurrent.futures.as_completed(futures)):
            res = f.result()
            if res:
                k_name = raw_candidates[i][2]
                # 每个频道保留最多 15 个链接，总有一个能播！
                if k_name not in results: results[k_name] = []
                if len(results[k_name]) < 15:
                    results[k_name].append(res)

    # 写入文件
    content = "#EXTM3U\n"
    for k in keyword_map.keys():
        if k in results:
            for item in results[k]:
                content += f"{item['info']}\n{item['url']}\n"

    with open("ipv4_only.m3u", "w", encoding="utf-8") as f:
        f.write(content)
    with open("integrated_list.m3u", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_process()
  





