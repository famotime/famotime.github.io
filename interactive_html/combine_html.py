"""
将多个html文件合并成一个html文件
- 读取指定目录下的所有html文件
- 逐个读取html文件中的<head>内容，删除重复的<head>内容，合并不同的内容
- 逐个读取html文件中的<body>标签，将<body>标签中的内容合并成一个<body>标签
- 直接合并<body>内容
- 将合并后的<head>和<body>内容写入新的combined.html文件
"""

from pathlib import Path
from bs4 import BeautifulSoup
from typing import Set, List, Optional
from fnmatch import fnmatch
import re

def get_unique_head_elements(soup: BeautifulSoup) -> Set[str]:
    """
    从BeautifulSoup对象中提取head元素的唯一内容

    Args:
        soup: BeautifulSoup对象
    Returns:
        head元素的集合
    """
    head_elements = set()
    if not soup.head:
        return head_elements

    # 提取所有有效的head子元素
    try:
        # 获取常见的标记元素
        meta_tags = [str(tag) for tag in soup.head.find_all('meta') if tag is not None]
        link_tags = [str(tag) for tag in soup.head.find_all('link') if tag is not None]
        script_tags = [str(tag) for tag in soup.head.find_all('script') if tag is not None]
        style_tags = [str(tag) for tag in soup.head.find_all('style') if tag is not None]
        title_tags = [str(tag) for tag in soup.head.find_all('title') if tag is not None]

        # 获取head中的其他元素（如base, noscript等）
        other_tags = []
        for tag in soup.head.children:
            if tag.name and tag.name not in ['meta', 'link', 'script', 'style', 'title']:
                other_tags.append(str(tag))

        # 合并所有标记
        all_tags = meta_tags + link_tags + script_tags + style_tags + title_tags + other_tags

        # 添加到集合
        for tag in all_tags:
            if tag.strip():
                head_elements.add(tag.strip())

        print(f"提取了 {len(meta_tags)} 个meta标签, {len(link_tags)} 个link标签, {len(script_tags)} 个script标签, {len(style_tags)} 个style标签, {len(title_tags)} 个title标签, {len(other_tags)} 个其他标签")
    except Exception as e:
        print(f"提取head元素时出错: {str(e)}")

    return head_elements

def get_body_content(soup: BeautifulSoup, file_name: str = "") -> str:
    """
    从BeautifulSoup对象中提取body内容，不添加任何包装

    Args:
        soup: BeautifulSoup对象
        file_name: 源文件名，用于标识内容来源（仅作记录用）
    Returns:
        body内容字符串
    """
    if not soup.body:
        return ""

    try:
        # 提取body内容
        content = ""
        try:
            content = soup.body.decode_contents().strip()
        except (AttributeError, TypeError) as e:
            print(f"获取body内容时出错: {e}")
            # 尝试替代方法获取body内容
            try:
                content = ''.join(str(content) for content in soup.body.contents)
            except Exception:
                content = str(soup.body)

        return content
    except Exception as e:
        print(f"处理body内容时出错: {e}")
        return ""

def combine_html_files(
    input_dir: Path,
    output_file: Path,
    file_pattern: str = "*.html",
    exclude_pattern: str = "combined*.html",
    encoding: str = 'utf-8',
    title: Optional[str] = None,
    lang: str = "zh-CN",
    enable_scrolling: bool = True,
    parser: str = 'html.parser',  # 添加解析器选项
    include_toc: bool = False     # 控制是否包含目录，默认为False
) -> None:
    """
    合并指定目录下的HTML文件

    Args:
        input_dir: 输入目录路径
        output_file: 输出文件路径
        file_pattern: 文件匹配模式，默认为"*.html"
        exclude_pattern: 要排除的文件模式，默认为"combined*.html"
        encoding: 文件编码，默认为'utf-8'
        title: 合并后文件的标题，默认为None
        lang: HTML语言属性，默认为"zh-CN"
        enable_scrolling: 是否启用滚动功能，默认为True
        parser: HTML解析器类型，默认为'html.parser'，可选 'lxml', 'html5lib'
        include_toc: 是否包含目录，默认为False
    """
    # 检查并尝试导入更好的解析器
    if parser != 'html.parser':
        try:
            if parser == 'lxml':
                import lxml
                print("使用lxml解析器")
            elif parser == 'html5lib':
                import html5lib
                print("使用html5lib解析器")
        except ImportError:
            print(f"警告: {parser}解析器不可用，回退到html.parser")
            parser = 'html.parser'

    # 获取所有匹配的html文件并排序
    try:
        html_files = sorted(list(input_dir.glob(file_pattern)))
        print(f"找到 {len(html_files)} 个匹配的HTML文件")
        for i, file in enumerate(html_files):
            print(f"  {i+1}. {file.name}")
    except Exception as e:
        print(f"查找HTML文件时出错: {str(e)}")
        return

    if not html_files:
        print(f"在 {input_dir} 中没有找到匹配的HTML文件")
        return

    # 排除已生成的合并文件
    original_count = len(html_files)

    # 排除输出文件（始终排除）
    output_file_name = output_file.name
    output_file_path = output_file.resolve()
    html_files = [f for f in html_files if (f.name != output_file_name and f.resolve() != output_file_path)]
    print(f"排除输出文件: {output_file_name}")

    # 基于exclude_pattern排除文件
    if exclude_pattern:
        html_files_before = len(html_files)
        html_files = [f for f in html_files if not fnmatch(f.name, exclude_pattern)]
        exclude_count = html_files_before - len(html_files)
        if exclude_count > 0:
            print(f"基于模式 '{exclude_pattern}' 排除了 {exclude_count} 个文件")

    if len(html_files) < original_count:
        excluded_count = original_count - len(html_files)
        print(f"总共排除了 {excluded_count} 个文件")
        print(f"实际处理的文件数量: {len(html_files)}")

    # 按文件名排序，确保处理顺序一致
    html_files = sorted(html_files, key=lambda f: f.name)

    # 存储合并的内容
    combined_head_elements = set()
    combined_body_content = []

    # 用于追踪已处理的脚本和样式，避免重复
    processed_scripts = set()
    processed_styles = set()

    # 处理每个HTML文件
    for i, html_file in enumerate(html_files):
        print(f"\n处理文件 {i+1}/{len(html_files)}: {html_file.name}")

        try:
            with html_file.open('r', encoding=encoding) as f:
                html_content = f.read()

                # 检查HTML内容是否为空
                if not html_content.strip():
                    print(f"警告: 文件 {html_file.name} 内容为空")
                    continue

                # 解析HTML
                try:
                    soup = BeautifulSoup(html_content, parser)
                except Exception as e:
                    print(f"HTML解析错误 {html_file.name}: {str(e)}")
                    print(f"尝试使用基本解析器...")
                    soup = BeautifulSoup(html_content, 'html.parser')

                # 收集head元素
                try:
                    head_elements = get_unique_head_elements(soup)
                    print(f"从 {html_file.name} 提取了 {len(head_elements)} 个头部元素")
                    combined_head_elements.update(head_elements)
                except Exception as e:
                    print(f"提取头部元素时出错 {html_file.name}: {str(e)}")

                # 收集body内容
                try:
                    body_content = get_body_content(soup, html_file.name)
                    if body_content:
                        combined_body_content.append(body_content)
                        print(f"成功提取 {html_file.name} 的body内容 ({len(body_content)} 字符)")
                    else:
                        print(f"警告: 未能从 {html_file.name} 提取body内容")
                except Exception as e:
                    print(f"提取body内容时出错 {html_file.name}: {str(e)}")

        except UnicodeDecodeError as e:
            print(f"Unicode解码错误 {html_file.name}: {str(e)}")
            print(f"尝试使用不同编码...")

            # 尝试不同的编码
            for alt_encoding in ['utf-8-sig', 'latin1', 'cp1252']:
                try:
                    with html_file.open('r', encoding=alt_encoding) as f:
                        html_content = f.read()
                        soup = BeautifulSoup(html_content, parser)
                        print(f"使用 {alt_encoding} 编码成功读取")

                        # 收集head元素
                        head_elements = get_unique_head_elements(soup)
                        print(f"从 {html_file.name} 提取了 {len(head_elements)} 个头部元素")
                        combined_head_elements.update(head_elements)

                        # 收集body内容
                        body_content = get_body_content(soup, html_file.name)
                        if body_content:
                            combined_body_content.append(body_content)
                            print(f"成功提取 {html_file.name} 的body内容")
                            break  # 成功找到正确的编码
                except Exception:
                    continue  # 尝试下一个编码
            else:
                print(f"无法找到合适的编码来读取 {html_file.name}")
        except Exception as e:
            print(f"处理文件 {html_file.name} 时出错: {str(e)}")
            continue

    print(f"\n合并了 {len(combined_head_elements)} 个唯一头部元素和 {len(combined_body_content)} 个body内容")

    # 如果没有指定标题，使用第一个文件的标题
    if not title and html_files:
        try:
            with html_files[0].open('r', encoding=encoding) as f:
                soup = BeautifulSoup(f.read(), parser)
                if soup.title and soup.title.string:
                    title = soup.title.string
                    print(f"使用第一个文件的标题: {title}")
                else:
                    title = "Combined HTML"
                    print("未找到标题，使用默认标题")
        except Exception as e:
            print(f"读取标题时出错: {str(e)}")
            title = "Combined HTML"

    # 添加启用滚动的CSS (简化版，不添加额外元素样式)
    scrolling_css = """
    <style>
        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
            overflow-y: auto !important;
            overflow-x: hidden;
        }
        /* 图片和多媒体元素响应式 */
        img, video, canvas, svg, iframe {
            max-width: 100%;
            height: auto;
        }
        /* 确保表格正确显示 */
        table {
            max-width: 100%;
            overflow-x: auto;
            display: block;
            border-collapse: collapse;
        }
        /* 确保代码块正确显示 */
        pre, code {
            white-space: pre-wrap;
            word-wrap: break-word;
            max-width: 100%;
            overflow-x: auto;
        }
    </style>
    """ if enable_scrolling else ""

    # 创建合并后的HTML文档
    combined_html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="{encoding}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {scrolling_css}
    {''.join(combined_head_elements)}
</head>
<body>
    {''.join(combined_body_content)}
</body>
</html>"""

    # 如果启用滚动功能，修复CSS
    if enable_scrolling:
        combined_html = fix_css_for_scrolling(combined_html)

    # 写入合并后的文件
    try:
        output_file.write_text(combined_html, encoding=encoding)
        print(f"合并完成! 输出文件: {output_file}")
    except Exception as e:
        print(f"写入输出文件时出错: {str(e)}")

    # 输出摘要信息
    print(f"摘要: 处理了 {len(html_files)} 个HTML文件，合并了 {len(combined_head_elements)} 个头部元素和 {len(combined_body_content)} 个body内容")

def fix_css_for_scrolling(html_content: str) -> str:
    """
    修复CSS以确保HTML页面可以正常滚动，不添加额外元素

    Args:
        html_content: HTML内容字符串
    Returns:
        修复后的HTML内容
    """
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 查找所有style标签
    style_tags = soup.find_all('style')

    for style_tag in style_tags:
        css_content = style_tag.string
        if css_content:
            # 修复可能阻止滚动的CSS属性
            # 1. 修复overflow属性
            css_content = re.sub(r'overflow\s*:\s*hidden', 'overflow: visible', css_content)
            css_content = re.sub(r'overflow-y\s*:\s*hidden', 'overflow-y: auto', css_content)
            css_content = re.sub(r'overflow-x\s*:\s*hidden', 'overflow-x: auto', css_content)

            # 2. 移除固定高度和宽度的限制
            css_content = re.sub(r'(body|html|\.slide|\.container|\.content)\s*{([^}]*)height\s*:\s*\d+[^;]*;', r'\1 {\2height: auto;', css_content)
            css_content = re.sub(r'(body|html|\.slide|\.container|\.content)\s*{([^}]*)min-height\s*:\s*\d+[^;]*;', r'\1 {\2min-height: auto;', css_content)
            css_content = re.sub(r'(body|html|\.slide|\.container|\.content)\s*{([^}]*)max-height\s*:\s*\d+[^;]*;', r'\1 {\2max-height: none;', css_content)

            # 3. 确保内容可以正常流动
            css_content = re.sub(r'position\s*:\s*fixed', 'position: relative', css_content)

            # 更新style标签内容
            style_tag.string = css_content

    # 修复可能存在的内联样式
    for tag in soup.find_all(lambda t: t.has_attr('style')):
        style_attr = tag['style']

        # 应用相同的修复规则到内联样式
        if 'overflow: hidden' in style_attr:
            style_attr = style_attr.replace('overflow: hidden', 'overflow: visible')

        if 'position: fixed' in style_attr:
            style_attr = style_attr.replace('position: fixed', 'position: relative')

        if 'height:' in style_attr and any(unit in style_attr for unit in ['px', 'vh', '%']):
            style_attr = re.sub(r'height\s*:\s*\d+[^;]*;', 'height: auto;', style_attr)

        tag['style'] = style_attr

    # 返回修复后的HTML
    return str(soup)

if __name__ == "__main__":
    # 定制化运行示例

    # 示例1：基本用法 - 合并指定目录下的所有HTML文件
    print("\n=== 示例1：基本用法 ===")
    input_directory = Path.cwd() / "MarkovModel"
    output_file = input_directory / "combined.html"

    print(f"输入目录: {input_directory}")
    print(f"输出文件: {output_file}")

    combine_html_files(
        input_directory,
        output_file,
        enable_scrolling=True,  # 启用滚动功能
        include_toc=False       # 不包含目录
    )

    """
    # 示例2：解决滚动问题 - 合并文件并确保可以滚动查看
    print("\n=== 示例2：解决滚动问题 ===")
    input_directory = Path.cwd() / "FourierTransformation"
    output_file = input_directory / "scrollable_combined.html"

    print(f"输入目录: {input_directory}")
    print(f"输出文件: {output_file}")

    combine_html_files(
        input_directory,
        output_file,
        file_pattern="Fourier*.html",          # 只合并以Fourier开头的HTML文件
        exclude_pattern="combined*.html",       # 排除已合并的文件
        title="傅里叶变换系列（可滚动版本）",   # 自定义标题
        enable_scrolling=True                   # 启用滚动功能
    )


    # 示例3：按特定顺序合并文件
    print("\n=== 示例3：按特定顺序合并文件 ===")
    input_directory = Path.cwd() / "FourierTransformation"
    output_file = input_directory / "ordered_combined.html"

    # 手动指定文件顺序
    specific_files = [
        input_directory / "FourierTransformation01.html",
        input_directory / "FourierTransformation02.html",
        input_directory / "FourierTransformation03.html"
    ]

    # 确保所有文件存在
    files_to_combine = [f for f in specific_files if f.exists()]

    if files_to_combine:
        # 创建一个临时目录
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # 将文件按序号复制到临时目录
            for i, file in enumerate(files_to_combine):
                temp_file = temp_dir_path / f"{i+1:02d}_{file.name}"
                shutil.copy(file, temp_file)

            # 合并临时目录中的文件（它们现在按数字顺序排序）
            combine_html_files(
                temp_dir_path,
                output_file,
                title="按顺序合并的傅里叶变换课程",
                enable_scrolling=True  # 启用滚动功能
            )
    else:
        print("未找到指定文件，无法按顺序合并")
    """

