import pathlib
import re

# 新增纵向排列样式检查和修改函数
def ensure_vertical_layout(content):
    # 检查是否有 body 样式设置纵向排列
    if 'display: flex;' not in content and 'flex-direction: column;' not in content:
        # 查找 head 标签结束位置
        head_end = content.find('</head>')
        if head_end != -1:
            # 在 head 中添加纵向排列样式
            style = '<style>body { display: flex; flex-direction: column; }</style>'
            content = content[:head_end] + style + content[head_end:]
    return content

# 定义工作目录
workspace_folder = pathlib.Path.cwd() / "FourierTransformation"

# 定义合并后的文件名
output_file = workspace_folder / 'combined.html'

# 获取当前目录下所有 HTML 文件
html_files = [file for file in workspace_folder.iterdir() if file.is_file() and file.suffix == '.html' and file.name != 'combined.html']

if not html_files:
    print('未找到 HTML 文件。')
else:
    # 初始化合并内容
    combined_content = ''
    head_found = False
    body_start_found = False
    body_end_count = 0

    for file in html_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

                # 新增纵向排列样式检查和修改
                content = ensure_vertical_layout(content)

                if not head_found:
                    # 提取第一个文件的头部
                    head_match = re.search(r'<!DOCTYPE html>.*?<head>.*?</head>', content, re.DOTALL)
                    if head_match:
                        combined_content += head_match.group()
                        head_found = True

                if not body_start_found:
                    # 提取第一个文件的 <body> 开始标签
                    body_start_match = re.search(r'<body.*?>', content)
                    if body_start_match:
                        combined_content += body_start_match.group()
                        body_start_found = True

                # 提取文件内容，去除头部和 <body> 标签
                body_content = re.sub(r'<!DOCTYPE html>.*?<body.*?>', '', content, flags=re.DOTALL)
                body_content = re.sub(r'</body>.*?</html>', '', body_content, flags=re.DOTALL)
                combined_content += body_content.strip()

                # 统计 </body> 标签数量
                body_end_count += content.count('</body>')

        except Exception as e:
            print(f'处理文件 {file} 时出错: {e}')

    # 添加最后一个 </body> 和 </html> 标签
    if body_start_found and body_end_count > 0:
        combined_content += '</body></html>'

    # 写入合并后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_content)

    print('HTML 文件合并完成。')