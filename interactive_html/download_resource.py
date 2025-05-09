import re
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse

def download_resources(html_content, output_folder, base_url=''):
    # 将html中所有的资源下载到指定文件夹中，并将html中的资源路径替换为本地相对路径

    # 定义需要下载的资源类型
    resource_patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\']',
        r'<script[^>]+src=["\']([^"\']+)["\']'
    ]

    # 创建输出文件夹
    output_path = Path(output_folder)
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    # 查找所有资源链接
    all_links = []
    for pattern in resource_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        all_links.extend(matches)

    # 下载资源并替换路径
    for link in set(all_links):
        # 解析绝对链接
        absolute_url = urljoin(base_url, link)
        parsed_url = urlparse(absolute_url)
        path = parsed_url.path
        filename = Path(path).name
        local_path = Path(output_folder) / filename

        # 检查文件是否已存在，若存在则跳过下载
        if local_path.exists():
            print(f'{local_path} 已存在，跳过下载。')
            # 替换 HTML 中的路径
            html_content = html_content.replace(link, local_path.relative_to(output_folder.parent).as_posix())
            continue

        # 下载资源
        try:
            response = requests.get(absolute_url)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                # 替换 HTML 中的路径
                html_content = html_content.replace(link, local_path.relative_to(output_folder.parent).as_posix())
        except Exception as e:
            print(f'下载 {absolute_url} 失败: {e}')

    return html_content


if __name__ == '__main__':
    workspace_folder = Path.cwd()
    html_file = workspace_folder / '傅里叶变换/傅里叶变换.html'
    output_folder = html_file.parent / 'assets'

    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        new_html_content = download_resources(html_content, output_folder, base_url='')
        new_html_file = html_file.with_name(html_file.stem + '_new.html')
        with open(new_html_file, 'w', encoding='utf-8') as f:
            f.write(new_html_content)
        print(f'已下载“{html_file}”的资源文件到本地，新文件另存为“{new_html_file}”')
    except Exception as e:
        print(f'处理 {html_file} 时出错: {e}')
