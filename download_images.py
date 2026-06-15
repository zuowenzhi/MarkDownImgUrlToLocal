import re
import os
import glob
import urllib.request
import urllib.error
import ssl

# 禁用SSL验证（飞书链接可能需要）
ssl._create_default_https_context = ssl._create_unverified_context

# 脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(script_dir, "assets")

# 确保assets目录存在
os.makedirs(assets_dir, exist_ok=True)

# 扫描脚本同级目录下的所有 .md 文件
md_files = glob.glob(os.path.join(script_dir, "*.md"))
print(f"共找到 {len(md_files)} 个 md 文件")

# 收集所有 md 文件中的图片 URL（去重），并按 md 文件名编号
url_to_local = {}   # url -> 本地相对路径
url_to_stem = {}    # url -> (md_stem, index)  用于按 md 文件名命名

for md_file in md_files:
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r'!\[.*?\]\((https?://[^)]+)\)'
    matches = re.findall(pattern, content)

    # md 文件名（不含扩展名）作为图片前缀
    md_stem = os.path.splitext(os.path.basename(md_file))[0]
    img_idx = 0
    for url in matches:
        if url not in url_to_local:
            img_idx += 1
            url_to_local[url] = None  # 占位，下载后填充
            url_to_stem[url] = (md_stem, img_idx)

    print(f"  {os.path.basename(md_file)}: 找到 {len(matches)} 张图片")

unique_urls = list(url_to_local.keys())
print(f"\n去重后共 {len(unique_urls)} 张图片需要下载")

# 下载每张图片
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

success_count = 0
fail_count = 0

for i, url in enumerate(unique_urls, 1):
    # 根据 md 文件名 + 数字来命名
    md_stem, img_idx = url_to_stem[url]
    filename = f"{md_stem}_{img_idx:03d}.png"
    filepath = os.path.join(assets_dir, filename)

    print(f"[{i}/{len(unique_urls)}] 正在下载: {filename}...", end=" ")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            # 根据实际content-type确定扩展名
            content_type = response.headers.get("Content-Type", "")
            if "jpeg" in content_type or "jpg" in content_type:
                ext = ".jpg"
            elif "png" in content_type:
                ext = ".png"
            elif "gif" in content_type:
                ext = ".gif"
            elif "webp" in content_type:
                ext = ".webp"
            else:
                ext = ".png"  # 默认png

            filename = f"{md_stem}_{img_idx:03d}{ext}"
            filepath = os.path.join(assets_dir, filename)

            with open(filepath, "wb") as img_file:
                img_file.write(data)

            # 记录 URL -> 本地相对路径的映射
            local_path = f"assets/{filename}"
            url_to_local[url] = local_path

            print(f"成功 ({len(data)} bytes) -> {filename}")
            success_count += 1
    except Exception as e:
        print(f"失败: {e}")
        fail_count += 1

# 替换每个 md 文件中的图片链接
if success_count > 0:
    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        replaced = False
        for url, local_path in url_to_local.items():
            if local_path and url in content:
                content = content.replace(url, local_path)
                replaced = True

        if replaced:
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"已更新: {os.path.basename(md_file)}")
else:
    print("\n没有成功下载任何图片，跳过 md 文件更新")

print(f"\n完成! 成功: {success_count}, 失败: {fail_count}")
