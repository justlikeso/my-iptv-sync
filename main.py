import requests
import re

# 1. 扩充更强力的源站（包含港台、国际频道）
SOURCES = [
    "https://raw.githubusercontent.com/Guovin/TV/gd/output/result.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u",
    "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    "https://raw.githubusercontent.com/Meroser/IPTV/main/IPTV.m3u"
]

def get_favorites():
    # 读取收藏夾并去掉空格
    with open("favorites.txt", "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def fetch_and_filter():
    favs = get_favorites()
    print(f"正在查找以下频道: {favs}")
    
    output_lines = ["#EXTM3U"]
    found_count = 0
    
    for url in SOURCES:
        try:
            print(f"正在抓取源: {url}")
            response = requests.get(url, timeout=15)
            content = response.text.split('\n')
            
            for i in range(len(content)):
                line = content[i]
                if "#EXTINF" in line:
                    # 检查这一行是否包含我们的关键词
                    for fav in favs:
                        # 忽略大小写匹配
                        if fav.lower() in line.lower():
                            # 找到后，把信息行和紧接着的 URL 行都存入
                            if i + 1 < len(content) and content[i+1].startswith("http"):
                                output_lines.append(line)
                                output_lines.append(content[i+1])
                                found_count += 1
                                break # 匹配到一个关键词就跳过，防止重复添加
        except Exception as e:
            print(f"连接失败 {url}: {e}")

    # 保存结果
    with open("my_list.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    
    print(f"任务完成！总共找到 {found_count} 个符合条件的频道。")

if __name__ == "__main__":
    fetch_and_filter()
  
  
