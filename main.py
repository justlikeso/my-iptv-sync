import requests
import concurrent.futures

# 1. 扩充源列表
SOURCES = [
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv.m3u",
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u",
    "https://raw.githubusercontent.com/FongMi/TV/main/itv/iptv.m3u",
    "https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u",
    "https://raw.githubusercontent.com/Meroser/IPTV/main/IPTV.m3u"
]

# 2. 【核心改动】硬编码保底源 - 这些是目前大陆直连最稳的高清源
MUST_HAVE = [
    {"name": "凤凰中文 HD", "url": "http://117.148.179.136/hw-ott-n-test.miguvideo.com/PLTV/88888888/224/3221225829/index.m3u8"},
    {"name": "凤凰资讯 HD", "url": "http://117.148.179.136/hw-ott-n-test.miguvideo.com/PLTV/88888888/224/3221225830/index.m3u8"},
    {"name": "HBO 高清", "url": "http://103.233.254.164:2042/live/hbo.m3u8"},
    {"name": "Discovery 探索", "url": "http://103.233.254.164:2042/live/discovery.m3u8"},
    {"name": "国家地理 HD", "url": "http://103.233.254.164:2042/live/natgeo.m3u8"},
    {"name": "纬来体育", "url": "http://103.233.254.164:2042/live/vlsport.m3u8"},
    {"name": "纬来电影", "url": "http://103.233.254.164:2042/live/vmovie.m3u8"}
]

def clean_url(url):
    return url.split('$')[0].split(' ')[0].strip()

def check_url(info, url):
    url = clean_url(url)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        with requests.get(url, timeout=3, stream=True, headers=headers) as r:
            if r.status_code == 200:
                return {"info": info, "url": url}
    except:
        pass
    return None

def fetch_and_process():
    # 关键词匹配
    keyword_map = {
        "凤凰": ["凤凰", "Phoenix"],
        "HBO": ["HBO"],
        "Discovery": ["Discovery", "探索"],
        "国家地理": ["National", "地理", "Nat Geo"],
        "纬来": ["纬来", "Videoland"],
        "国兴": ["国兴"],
        "翡翠": ["翡翠", "TVB"],
        "NHK": ["NHK"]
    }

    try:
        with open("favorites.txt", "r", encoding="utf-8") as f:
            user_keys = [l.strip() for l in f if l.strip()]
    except:
        user_keys = list(keyword_map.keys())

    # 结果去重字典
    results = {}

    # A. 先加载保底必看台
    for item in MUST_HAVE:
        results[item['name']] = {"info": f"#EXTINF:-1,{item['name']}", "url": item['url']}

    # B. 抓取网络源并补充
    raw_candidates = []
    for s_url in SOURCES:
        try:
            r = requests.get(s_url, timeout=10)
            lines = r.text.split('\n')
            for i in range(len(lines)):
                if "#EXTINF" in lines[i]:
                    for k in user_keys:
                        matches = keyword_map.get(k, [k])
                        if any(m.lower() in lines[i].lower() for m in matches):
                            if i + 1 < len(lines) and lines[i+1].startswith("http"):
                                raw_candidates.append((lines[i], lines[i+1].strip(), k))
                                break
        except: continue

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_url, info, url) for info, url, k in raw_candidates]
        for i, f in enumerate(concurrent.futures.as_completed(futures)):
            res = f.result()
            if res:
                k_name = raw_candidates[i][2]
                # 每个关键词下再增加 2 个不同线路，避免重复
                unique_key = f"{k_name}_{i}" 
                if len([x for x in results if k_name in x]) < 4: 
                    results[unique_key] = res

    # C. 生成 M3U (加入 PotPlayer 兼容前缀)
    content = "#EXTM3U\n"
    for item in results.values():
        content += f"{item['info']}\n{item['url']}\n"

    with open("ipv4_only.m3u", "w", encoding="utf-8") as f:
        f.write(content)
    with open("integrated_list.m3u", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    fetch_and_process()




