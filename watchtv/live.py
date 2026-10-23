import os
import re
import requests

# 远程源地址
URL = "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/zubo_all.txt"
# 输出路径
OUTPUT_PATH = "watchtv/live.m3u8"

def fetch_and_filter_iptv():
    print(f"正在请求远程源: {URL}")
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        content = response.text
    except Exception as e:
        print(f"获取远程源失败: {e}")
        return

    lines = content.splitlines()
    
    # 正则表达式：匹配包含日期和“更新”字样的行（时间动态分组标题）
    time_pattern = re.compile(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}.*?更新')

    # 用于暂存所有清洗后的有效频道：元素格式为 (channel_name, channel_url)
    valid_channels = []
    
    skip_current_group = False

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        # 检查这一行是否是新的分组标题（通常含有 #genre#）
        if "#genre#" in stripped_line:
            if time_pattern.search(stripped_line):
                skip_current_group = True  # 开启屏蔽状态（针对时间更新分组）
                continue
            else:
                skip_current_group = False # 遇到其他正常分组，解除屏蔽
            continue

        # 如果当前正处于需要屏蔽的分组中，跳过
        if skip_current_group:
            continue

        # 备用关键词过滤
        if any(keyword in stripped_line for keyword in ["最后更新", "公众号", "長期有效"]):
            continue

        # 解析频道行（形如：频道名,播放地址）
        if "," in stripped_line:
            parts = stripped_line.split(",", 1)
            name = parts[0].strip()
            url = parts[1].strip()
            if name and url:
                valid_channels.append((name, url))

    print(f"共筛选出 {len(valid_channels)} 个有效频道，正在转换为标准 M3U8 格式并统一归入【IPTV组播源】...")

    # 组装标准的 M3U8 文件内容
    m3u8_lines = ["#EXTM3U"]
    
    for name, url in valid_channels:
        # 统一设置分组名称为 "IPTV组播源"
        extinf_line = f'#EXTINF:-1 group-title="IPTV组播源",{name}'
        m3u8_lines.append(extinf_line)
        m3u8_lines.append(url)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # 写入文件
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u8_lines) + "\n")
    
    print(f"转换完成，文件已成功保存至: {OUTPUT_PATH}")

if __name__ == "__main__":
    fetch_and_filter_iptv()
