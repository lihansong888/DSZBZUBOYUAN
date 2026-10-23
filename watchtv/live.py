import os
import re
import requests

# 远程源地址
URL = "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/zubo_all.txt"
# 输出路径（对应 GitHub Actions 中 git add 的文件）
OUTPUT_PATH = "watchtv/live.m3u8"

def fetch_and_filter_iptv():
    print(f"正在请求远程源: {URL}")
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        # 确保编码正确，防止中文乱码
        response.encoding = response.apparent_encoding
        content = response.text
    except Exception as e:
        print(f"获取远程源失败: {e}")
        return

    lines = content.splitlines()
    filtered_lines = []
    skipped_count = 0

    # 正则表达式：精准匹配类似 "2026/10/23 21:51更新,#genre#" 这种动态时间分组行
    time_pattern = re.compile(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}.*?更新')

    # 用于控制是否处于“屏蔽当前分组及其内容”的状态
    skip_current_group = False

    for line in lines:
        stripped_line = line.strip()

        # 检查这一行是否是新的分组标题（通常含有 #genre#）
        if "#genre#" in stripped_line:
            # 判断这个新分组是不是我们要屏蔽的时间更新分组
            if time_pattern.search(stripped_line):
                skip_current_group = True  # 开启屏蔽状态
                skipped_count += 1
                continue
            else:
                skip_current_group = False # 遇到了其他正常分组，关闭屏蔽状态

        # 如果当前正处于需要屏蔽的分组中，则把该分组下的所有频道内容全部跳过
        if skip_current_group:
            skipped_count += 1
            continue

        # 备用关键词过滤
        if any(keyword in stripped_line for keyword in ["最后更新", "公众号", "長期有效"]):
            skipped_count += 1
            continue

        filtered_lines.append(line)

    print(f"处理完成，共连同时间分组及所属内容一起过滤掉了 {skipped_count} 行。")

    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # 写入文件
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(filtered_lines) + "\n")
    
    print(f"文件已成功保存至: {OUTPUT_PATH}")

if __name__ == "__main__":
    fetch_and_filter_iptv()
