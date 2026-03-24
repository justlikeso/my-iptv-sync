import requests
import concurrent.futures

# 1. 再次扩充源列表，加入更多国际频道库
SOURCES = [
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv.m3u",
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u",
    "https://raw.githubusercontent.com/FongMi/TV/main/itv/iptv.m3u",
    "https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u",
    "https://raw.githubusercontent.com/Meroser/IPTV/main/IPTV.m3u",
    "https://raw.githubusercontent.com/ssili126/tv/main/itvlist.m3u" # 新增：含大量国际台
]

# 2. 保底源保持不变
BACKUP_CHANNELS = [
    ("#EXTINF:-1,凤凰中文 (1080P)", "http://117.148.179.136/hw-ott-n-test.miguvideo.com/PLTV/88888888/224/3221225829/index.m3u8"),
    ("#EXTINF:-1,凤凰资讯 (1080P)", "http://117.148.179.136/hw-ott-n-test.miguvideo.com/PLTV/88888888/224/3221225830/index.m3u8")
]

def clean_url(url):
    """清洗URL，剪掉所有乱码后缀"""
    return url.split('$')[0].split(' ')[0].split('#')[0].split('?')[0].strip() if ".m3u8" not in url.split('?')[1] if '?' in url else url.split('$')[0].split(' ')[0].strip()

def check_url(info, url):
    url = clean_url(url)
    is_ipv6 = "[" in url or "ipv6" in url.lower()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        # 针对国际源，增加超时到 5 秒
        with requests.get(url, timeout=5, stream=True, headers=headers, allow_redirects=True) as r:
            if r.status_code == 200:
                next(r.iter_content(chunk_size=512))
                return {"info": info, "url": url, "is_ipv6": is_ipv6}
    except:
        pass
    return None

def fetch_and_process():
    # 扩展关键词匹配，增加英文缩写以提高 HBO 等台的命中率
    keyword_map = {
        "凤凰": ["凤凰", "Phoenix"],
        "HBO": ["HBO"],
        "Discovery": ["Discovery", "探索", "Disc"],
        "国家地理": ["National", "地理", "Nat Geo"],
        "纬来": ["纬来", "Videoland"],
        "国兴": ["国兴", "Kokusai"],
        "翡翠": ["翡翠", "TVB"],
        "NHK": ["NHK"]
    }

    try:
        with open("favorites.txt", "r", encoding="utf-8") as f:
            user_keys = [l.strip() for l in f if l.strip()]
    except:
        user_keys = list(keyword_map.keys())

    # 存储结果：每个台保留前 5 个最稳的线路
    final_dict = {} 

    # A. 抓取网络源
    raw_candidates = []
    for s_url in SOURCES:
        try:
            r = requests.get(s_url, timeout=10)
            lines = r.text.split('\n')
            for i in range(len(lines)):
                if "#EXTINF" in lines[i]:
                    for main_key in user_keys:
                        # 检查主关键词或其关联的英文词
                        match_list = keyword_map.get(main_key, [main_key])
                        if any(m.lower() in lines[i].lower() for m in match_list):
                            if i + 1 < len(lines) and lines[i+1].startswith("http"):
                                raw_candidates.append((lines[i], lines[i+1].strip(), main_key))
                                break
        except: continue

    # B. 多线程测速
    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        futures = [executor.submit(check_url, info, url) for info, url, k in raw_candidates]
        for i, f in enumerate(concurrent.futures.as_completed(futures)):
            res = f.result()
            if res:
                k = raw_candidates[i][2]
                if k not in final_dict: final_dict[k] = []
                if len(final_dict[k]) < 5: # 每个台留5个备份，防止有的播不了
                    final_dict[k].append(res)

    # C. 写入文件
    for file_name, ipv6_allowed in [("integrated_list.m3u", True), ("ipv4_only.m3u", False)]:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            # 写入保底
            for info, b_url in BACKUP_CHANNELS:
                f.write(f"{info}\n{b_url}\n")
            # 写入抓取结果
            for k in user_keys:
                if k in final_dict:
                    for item in final_dict[k]:
                        if not ipv6_allowed and item['is_ipv6']: continue
                        f.write(f"{item['info']}\n{item['url']}\n")
    
    print(f"筛选完毕。")

if __name__ == "__main__":
    fetch_and_process()


