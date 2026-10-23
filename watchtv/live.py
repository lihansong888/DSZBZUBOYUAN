import requests
import re
import os

# 源地址
url = "https://raw.githubusercontent.com/q1017673817/iptvz/refs/heads/main/zubo_all.txt"
# 匹配形如 2026/10/24  03:30更新 的分组名称
filter_re = re.compile(r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}更新")

def main():
    unique = set()
    result = ["#EXTM3U"]
    current_group = ""
    try:
        resp = requests.get(url, timeout=25)
        all_lines = resp.text.splitlines()
        for line in all_lines:
            line = line.strip()
            if not line:
                continue
            # 识别分组行（#开头）
            if line.startswith("#"):
                group_name = line.lstrip("#")
                if filter_re.search(group_name):
                    # 命中时间更新分组，屏蔽，清空当前分组
                    current_group = ""
                else:
                    current_group = group_name
            else:
                # 直播链接行，如果当前分组有效，加入列表
                if not current_group:
                    continue
                mark = f"{current_group}_{line}"
                if mark not in unique:
                    unique.add(mark)
                    result.append(f'#EXTINF:-1 group-title="{current_group}",{current_group}')
                    result.append(line)

        # 输出同目录下 iptvz.m3u8
        out_file = os.path.join(os.path.dirname(__file__), "iptvz.m3u8")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("\n".join(result))
        print(f"✅ 完成，一共 {len(unique)} 条有效频道")
    except Exception as err:
        print(f"❌ 异常：{err}")

if __name__ == "__main__":
    main()
