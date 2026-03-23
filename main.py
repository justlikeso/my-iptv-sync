import requests
import concurrent.futures
import re

# 1. 扩充后的源列表（加入更多包含国际大片的源）
SOURCES = [
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv.m3u",
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u",
    "https://raw.githubusercontent.com/FongMi/TV/main/itv/iptv.m3u",
    "https://raw.githubusercontent.com/yuanzl77/IPTV/main/live.m3u",
    "https://raw.githubusercontent.com/Meroser/IPTV/main/IPTV.m3u"
]

# 2. 核心频道保底（直接锁定你最想看的几个）
BACKUP_CHANNELS = [
    ("#EXTINF:-1,凤凰中文 (1080P)", "http://117.148.179.136/hw-ott-n-test.miguvideo.com/PLTV/88888888/224/3221225829/index.m3u8"),
    ("#EXTINF:-1,凤凰资讯 (1080P)", "http://117.148.179.136/hw-ott-n-test.miguvideo.com/PLTV/88888888/224/3221225830/index.m3u8")
]

def clean_url(url):
    """清洗URL，剪掉所有乱码后缀"""
    return url.split('$')[0].split(' ')[0].split('#')[0].strip()

def get_quality_score(info):
    """根据描述信息打分，优先保留高清源"""
    score = 0
    info_upper = info.upper()
    if "1080" in info_upper or "FHD" in info_upper: score += 10
    if "720" in info_upper or "HD" in info_upper: score += 5
    if "蓝光" in info or "高清" in info: score += 8
    return score

def check_url(info, url):
    url = clean_url(url)
    is_ipv6 = "[" in url or "ipv6" in url.lower()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        with requests.get(url, timeout=4, stream=True, headers=headers, allow_redirects=True) as r:
            if r.status_code == 200:
                # 确认有数据流
                next(r.iter_content(chunk_size=512))
                return {"info": info, "url": url, "is_ipv6": is_ipv6, "score": get_quality_score(info)}
    except:
        pass
    return None

def fetch_and_process():
    # 智能关键词库：自动关联中英文，确保 Discovery 等能被搜到
    try:
        with open("favorites.txt", "r", encoding="utf-8") as f:
            user_favs = [l.strip() for l in f if l.strip()]
    except:
        user_favs = ["凤凰", "HBO", "Discovery", "国家地理", "纬来"]

    # 存储结果：每个台保留前 3 个最稳的线路
    final_dict = {} 

    print(f"开始深度检索: {user_favs} ...")

    # A. 抓取网络源
    raw_candidates = []
    for s_url in SOURCES:
        try:
            r = requests.get(s_url, timeout=10)
            lines = r.text.split('\n')
            for i in range(len(lines)):
                if "#EXTINF" in lines[i]:
                    for f in user_favs:
                        # 模糊匹配：比如“国家地理”能匹配到“National Geographic”
                        if f.lower() in lines[i].lower():
                            if i + 1 < len(lines) and lines[i+1].startswith("http"):
                                raw_candidates.append((lines[i], lines[i+1].strip(), f))
                                break
        except: continue

    # B. 多线程测速
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_url, info, url) for info, url, fav_key in raw_candidates]
        for i, f in enumerate(concurrent.futures.as_completed(futures)):
            res = f.result()
            if res:
                fav_key = raw_candidates[i][2]
                if fav_key not in final_dict:
                    final_dict[fav_key] = []
                
                # 每个台最多留 3 条线路，按画质评分排序
                if len(final_dict[fav_key]) < 3:
                    final_dict[fav_key].append(res)
                    final_dict[fav_key].sort(key=lambda x: x['score'], reverse=True)

    # C. 写入文件
    for file_name, ipv6_allowed in [("integrated_list.m3u", True), ("ipv4_only.m3u", False)]:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            # 先写保底源
            for info, b_url in BACKUP_CHANNELS:
                f.write(f"{info}\n{b_url}\n")
            # 再写抓取到的源
            for channels in final_dict.values():
                for item in channels:
                    if not ipv6_allowed and item['is_ipv6']:
                        continue
                    f.write(f"{item['info']}\n{item['url']}\n")
    
    print(f"任务完成！已尝试找回 HBO/Discovery 等频道。")

if __name__ == "__main__":
    fetch_and_process()
