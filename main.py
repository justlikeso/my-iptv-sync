import requests
import re

# 1. 定义公开的聚合源（这里可以搜集更多 github 上的 m3u 链接）
SOURCES = [
    "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u"
]

def get_favorites():
    with open("favorites.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def fetch_and_filter():
    favs = get_favorites()
    output_lines = ["#EXTM3U"]
    
    for url in SOURCES:
        try:
            response = requests.get(url, timeout=10)
            content = response.text.split('\n')
            
            for i in range(len(content)):
                # 如果这一行包含频道信息
                if "#EXTINF" in content[i]:
                    # 检查是否包含你收藏的关键字
                    for fav in favs:
                        if fav.lower() in content[i].lower():
                            output_lines.append(content[i])      # 频道信息行
                            output_lines.append(content[i+1])    # 播放地址行
        except Exception as e:
            print(f"抓取 {url} 失败: {e}")

    # 保存结果
    with open("my_list.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

if __name__ == "__main__":
    fetch_and_filter()
  
