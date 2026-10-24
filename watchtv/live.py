import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 远程源地址
URL = "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/zubo_all.txt"
# 输出路径
OUTPUT_PATH = "watchtv/live.m3u8"
# 线程池并发数调整为 15，降低服务器压力防误判
MAX_WORKERS = 15
# 检测链接超时的秒数调整为 8 秒
TIMEOUT_SECONDS = 5

def check_url(channel_info):
    """检测单个直播源是否有效"""
    name, url = channel_info
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS, stream=True)
        if response.status_code < 400:
            return (name, url, True)
    except Exception:
        pass
    
    return (name, url, False)

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
    
    # 正则表达式：匹配包含日期和“更新”字样的行（动态时间分组标题）
    time_pattern = re.compile(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}.*?更新')

    raw_channels = []
    skip_current_group = False

    # 第一阶段：解析文本并应用状态机屏蔽时间更新分组及其所属内容
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        if "#genre#" in stripped_line:
            if time_pattern.search(stripped_line):
                skip_current_group = True
                continue
            else:
                skip_current_group = False
            continue

        if skip_current_group:
            continue

        if any(keyword in stripped_line for keyword in ["最后更新", "公众号", "長期有效"]):
            continue

        if "," in stripped_line:
            parts = stripped_line.split(",", 1)
            name = parts[0].strip()
            url = parts[1].strip()
            if name and url:
                raw_channels.append((name, url))

    print(f"解析到原始有效频道共 {len(raw_channels)} 个，开始进行纯 URL 去重...")

    # 第二阶段：纯 URL 去重（相同链接只保留一个，同名但不同链接全部保留）
    seen_urls = set()
    deduplicated_channels = []
    for name, url in raw_channels:
        if url not in seen_urls:
            seen_urls.add(url)
            deduplicated_channels.append((name, url))

    print(f"去重后剩余 {len(deduplicated_channels)} 个频道，开始进行多线程连通性检测（去失效）...")

    # 第三阶段：多线程并发检测（剔除死链）
    valid_channels = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_url, item): item for item in deduplicated_channels}
        
        completed_count = 0
        total_count = len(deduplicated_channels)
        
        for future in as_completed(futures):
            completed_count += 1
            name, url, is_valid = future.result()
            if is_valid:
                valid_channels.append((name, url))
            
            if completed_count % 20 == 0 or completed_count == total_count:
                print(f"检测进度: {completed_count}/{total_count} (有效: {len(valid_channels)})")

    print(f"检测完成！最终有效频道数: {len(valid_channels)}，正在组装标准的 M3U8 格式...")

    # 第四阶段：转换为标准 M3U8 格式，并统一归入【IPTV组播源】分组
    m3u8_lines = ["#EXTM3U"]
    for name, url in valid_channels:
        extinf_line = f'#EXTINF:-1 group-title="IPTV组播源",{name}'
        m3u8_lines.append(extinf_line)
        m3u8_lines.append(url)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u8_lines) + "\n")
    
    print(f"全部流程结束，文件已成功保存至: {OUTPUT_PATH}")

if __name__ == "__main__":
    fetch_and_filter_iptv()
