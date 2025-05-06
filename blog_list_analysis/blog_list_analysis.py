import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ast # 用于安全地计算字符串字面量
import numpy as np
from pathlib import Path
from collections import Counter as CollectionCounter # 别名以避免与 DataFrame.counter 冲突


# --- 安全字面量计算的辅助函数 ---
def safe_literal_eval(val):
    """
    安全地计算包含 Python 字面量（如列表、字典）的字符串。
    如果解析失败，则返回 None。
    """
    try:
        return ast.literal_eval(val)
    except (ValueError, SyntaxError, TypeError):
        # 如果 val 已经是非字符串类型（如 float (NaN)），可能会发生 TypeError
        if isinstance(val, (list, dict)): # 如果它已经是目标类型，则直接返回
            return val
        return None

# --- 1. 数据加载和初始设置 ---
print("开始数据加载...")
file_path = Path("blog_list.xlsx") # 确保 CSV 文件在同一目录中，或提供完整路径

if not file_path.exists():
    print(f"错误：文件 '{file_path}' 未找到。请检查文件名和路径。")
    exit()

try:
    df = pd.read_excel(file_path)
    print(f"文件 '{file_path}' 加载成功。")
except Exception as e:
    print(f"读取 CSV 文件时出错: {e}")
    exit()

# --- 2. 数据预处理 ---
print("开始数据预处理...")

# 将 inf 转换为 NaN
df = df.replace([np.inf, -np.inf], np.nan)

# 2.1 解析 'counter' 列（字典的字符串表示）
df['counter_dict'] = df['counter'].apply(safe_literal_eval)

# 提取单个计数，如果解析失败或键缺失，则默认为 0
df['commentCount'] = df['counter_dict'].apply(lambda x: x.get('commentCount', 0) if isinstance(x, dict) else 0)
df['likeCount'] = df['counter_dict'].apply(lambda x: x.get('likeCount', 0) if isinstance(x, dict) else 0)
df['readCount'] = df['counter_dict'].apply(lambda x: x.get('readCount', 0) if isinstance(x, dict) else 0)
df['shareCount'] = df['counter_dict'].apply(lambda x: x.get('shareCount', 0) if isinstance(x, dict) else 0)

# 2.2 将时间列转换为 datetime 对象
# 如果 'updateTime' 有额外信息（如示例中可能有换行符），则清理它
df['updateTime_cleaned'] = df['updateTime'].astype(str).apply(lambda x: x.split('\n')[0].strip())
df['createTime'] = pd.to_datetime(df['createTime'], errors='coerce')
df['updateTime'] = pd.to_datetime(df['updateTime_cleaned'], errors='coerce')

# 2.3 解析 'id_links' 列（列表的字符串表示）
df['id_links_list'] = df['id_links'].apply(safe_literal_eval)
# 确保它是一个列表，如果解析失败或不是列表，则默认为空列表
df['id_links_list'] = df['id_links_list'].apply(lambda x: x if isinstance(x, list) else [])

# 2.4 确保 'id' 是整数
df['id'] = df['id'].astype(int)

# 2.5 将 'pCategoryLocation' 转换为字符串，以便进行一致的分类绘图
df['pCategoryLocation'] = df['pCategoryLocation'].astype(str)

# 2.6 处理类似布尔值的列（elite, top, isMarkdown）
# 如果它们还不是布尔值，则转换为布尔值，或者处理字符串 'True'/'False'
for col in ['elite', 'top', 'isMarkdown']:
    if df[col].dtype == 'object': # 如果它是字符串
        df[col] = df[col].astype(str).str.lower().map({'true': True, 'false': False, '0': False, '1': True}).fillna(False)
    else: # 如果它已经是布尔值或整数（0/1）
        df[col] = df[col].astype(bool)


print("数据预处理完成。")
print(f"数据共有 {df.shape[0]} 行, {df.shape[1]} 列。")
print("\n处理后的数据概览 (前 5 行，部分列):")
print(df[['id', 'title', 'createTime', 'commentCount', 'likeCount', 'readCount', 'shareCount', 'pCategoryLocation', 'id_links_list', 'elite', 'top']].head())

# --- Matplotlib 中文字体配置 ---
# 确保 Matplotlib 可以正确显示中文字符。
# 您可能需要安装中文字体并更新下面的字体名称。
# 常见字体：'SimHei', 'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC'
try:
    # 设置中文字体并确保特殊字符正确显示
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'FangSong']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['mathtext.fontset'] = 'stix'
    plt.rcParams['mathtext.default'] = 'regular'
    plt.rcParams['axes.formatter.use_mathtext'] = True
    plt.rcParams['text.usetex'] = False

    # 显式处理负号显示
    plt.rcParams['text.usetex'] = False
    plt.rcParams['axes.formatter.use_mathtext'] = True
except Exception as e:
    print(f"字体设置警告: 未能成功设置中文字体。图表中的中文可能无法正确显示。错误: {e}")
    print("请确保您已安装合适的中文字体，并在代码中指定正确的字体名称。")

# --- 3. 数据分析和可视化 ---
print("\n开始数据分析与可视化...")
output_dir = Path("blog_visualizations")
output_dir.mkdir(parents=True, exist_ok=True) # 创建用于保存图表的目录

# 3.1 博文发布数量随时间变化
plt.figure(figsize=(12, 6))
df['createTime'].dt.year.value_counts().sort_index().plot(kind='bar', color='skyblue', edgecolor='black')
plt.title('每年博文发布数量')
plt.xlabel('年份')
plt.ylabel('博文数量')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(output_dir / "blogs_per_year.png")
# plt.show()
print(f"图 1 (保存在 {output_dir / 'blogs_per_year.png'}): 展示了每年发布的博文数量。")

plt.figure(figsize=(14, 7))
df.set_index('createTime').resample('ME')['id'].count().plot(kind='line', marker='o', linestyle='-', color='coral')
plt.title('每月博文发布数量趋势')
plt.xlabel('月份')
plt.ylabel('博文数量')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(output_dir / "blogs_per_month_trend.png")
# plt.show()
print(f"图 2 (保存在 {output_dir / 'blogs_per_month_trend.png'}): 展示了每月博文发布的趋势。")

# 3.2 博文分类 (pCategoryLocation)
category_counts = df['pCategoryLocation'].value_counts().nlargest(10)
plt.figure(figsize=(12, 7))
sns.barplot(x=category_counts.index, y=category_counts.values, palette='viridis')
plt.title('博文数量按分类 (Top 10)')
plt.xlabel('分类 ID (pCategoryLocation)')
plt.ylabel('博文数量')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(output_dir / "blogs_per_category.png")
# plt.show()
print(f"图 3 (保存在 {output_dir / 'blogs_per_category.png'}): 展示了博文数量最多的前 10 个分类。")

# 3.3 博文参与度分析
engagement_metrics = ['readCount', 'likeCount', 'commentCount', 'shareCount']
plt.figure(figsize=(15, 10))
for i, metric in enumerate(engagement_metrics):
    plt.subplot(2, 2, i + 1)
    # 如有必要，过滤掉极端异常值以获得更好的可视化效果，或使用对数刻度
    # 为简单起见，在直方图的 y 轴上使用对数刻度
    # 在绘图前显式地将 inf 值转换为 NaN 以避免 FutureWarning
    df[metric] = df[metric].replace([np.inf, -np.inf], np.nan)
    df[metric] = pd.to_numeric(df[metric], errors='coerce')
    sns.histplot(df[metric], kde=True, bins=30, color=sns.color_palette("husl", 4)[i])
    plt.title(f'{metric} 分布情况')
    plt.xlabel(metric)
    plt.ylabel('频数')
    if df[metric].max() > 1000: # 如果最大值很大，则应用对数刻度
         plt.yscale('log')
plt.suptitle('博文参与度指标分布', fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.96]) # 调整布局以留出主标题的空间
plt.savefig(output_dir / "engagement_distribution.png")
# plt.show()
print(f"图 4 (保存在 {output_dir / 'engagement_distribution.png'}): 展示了各项参与度指标的分布。")

# 按阅读数排名的前 N 篇博文
top_n = 10
top_read_blogs = df.nlargest(top_n, 'readCount')
plt.figure(figsize=(12, 8))
sns.barplot(x='readCount', y='title', data=top_read_blogs, palette='coolwarm', dodge=False)
plt.title(f'阅读数最高的 Top {top_n} 博文')
plt.xlabel('阅读数')
plt.ylabel('博文标题')
plt.yticks(fontsize=9) # 如果标题较长，则调整字体大小
plt.tight_layout()
plt.savefig(output_dir / "top_read_blogs.png")
# plt.show()
print(f"图 5 (保存在 {output_dir / 'top_read_blogs.png'}): 展示了阅读数最高的 {top_n} 篇博文。")

# 参与度指标之间的关系（例如，阅读数与点赞数）
plt.figure(figsize=(10, 6))
# 如果数据框太大，则使用样本以避免重叠绘图
sample_df = df.sample(n=min(1000, len(df)), random_state=1) if len(df) > 1000 else df
sns.scatterplot(x='readCount', y='likeCount', data=sample_df, alpha=0.6, edgecolor='w', s=50)
plt.title('阅读数与点赞数关系 (抽样)')
plt.xlabel('阅读数 (对数)')
plt.ylabel('点赞数 (对数)')
plt.xscale('log')
plt.yscale('log')
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(output_dir / "read_vs_like_scatter.png")
# plt.show()
print(f"图 6 (保存在 {output_dir / 'read_vs_like_scatter.png'}): 通过散点图展示了阅读数和点赞数之间的关系。")

# 3.4 博文内容特征
# 原创性 (source)
plt.figure(figsize=(8, 6))
source_counts = df['source'].value_counts()
source_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
plt.title('博文来源分析 (原创性)')
plt.ylabel('') # 隐藏默认的 y 轴标签
plt.tight_layout()
plt.savefig(output_dir / "source_originality_pie.png")
# plt.show()
print(f"图 7 (保存在 {output_dir / 'source_originality_pie.png'}): 展示了原创与其他来源博文的占比。")

# 精华和置顶博文
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
sns.countplot(x='elite', data=df, ax=axes[0], palette='Set2', hue='elite')
axes[0].set_title('是否精华博文')
axes[0].set_xticklabels(['非精华', '精华'])

sns.countplot(x='top', data=df, ax=axes[1], palette='Set2', hue='top')
axes[1].set_title('是否置顶博文')
axes[1].set_xticklabels(['非置顶', '置顶'])

plt.suptitle('精华与置顶博文统计', fontsize=16)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(output_dir / "elite_top_counts.png")
# plt.show()
print(f"图 8 (保存在 {output_dir / 'elite_top_counts.png'}): 分别统计了精华博文和置顶博文的数量。")

# 精华博文与非精华博文的参与度对比
plt.figure(figsize=(8, 6))
sns.boxplot(x='elite', y='readCount', data=df, palette='Set3', hue='elite')
plt.title('精华与非精华博文阅读数对比')
plt.xlabel('是否精华')
plt.ylabel('阅读数 (对数)')
plt.xticks([0, 1], ['非精华', '精华'])
plt.yscale('log') # 由于可能存在偏态，使用对数刻度
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(output_dir / "elite_read_comparison_boxplot.png")
# plt.show()
print(f"图 9 (保存在 {output_dir / 'elite_read_comparison_boxplot.png'}): 对比了精华与非精华博文的阅读数分布。")

# 3.5 博文网络分析 (内部链接)
# 出度（一篇博文链接到其他文章的数量）
df['out_degree'] = df['id_links_list'].apply(len)
plt.figure(figsize=(10, 6))
sns.histplot(df['out_degree'], bins=max(1, df['out_degree'].max() + 1) , kde=False, color='purple') # 确保 bins 覆盖所有值
plt.title('博文出度分布 (链接到其他文章的数量)')
plt.xlabel('出度')
plt.ylabel('博文数量')
if df['out_degree'].max() > 0 : plt.yscale('log') # 如果有链接，则使用对数刻度
plt.tight_layout()
plt.savefig(output_dir / "out_degree_distribution.png")
# plt.show()
print(f"图 10 (保存在 {output_dir / 'out_degree_distribution.png'}): 展示了博文出度的分布。")

# 入度（一篇博文被其他文章链接的数量）
all_linked_ids_flat = [str(linked_id) for sublist in df['id_links_list'] for linked_id in sublist if linked_id] # 确保 linked_id 不为 None
in_degree_counts = CollectionCounter(all_linked_ids_flat)
df['in_degree'] = df['id'].astype(str).map(in_degree_counts).fillna(0).astype(int)

plt.figure(figsize=(10, 6))
sns.histplot(df['in_degree'], bins=max(1, df['in_degree'].max() + 1), kde=False, color='teal')
plt.title('博文入度分布 (被其他文章链接的数量)')
plt.xlabel('入度')
plt.ylabel('博文数量')
if df['in_degree'].max() > 0 : plt.yscale('log') # 如果有入链，则使用对数刻度
plt.tight_layout()
plt.savefig(output_dir / "in_degree_distribution.png")
# plt.show()
print(f"图 11 (保存在 {output_dir / 'in_degree_distribution.png'}): 展示了博文入度的分布。")

# 按入度排名的前 N 篇博文
top_in_degree_blogs = df.nlargest(top_n, 'in_degree')
if not top_in_degree_blogs.empty and top_in_degree_blogs['in_degree'].max() > 0:
    plt.figure(figsize=(12, 8))
    sns.barplot(x='in_degree', y='title', data=top_in_degree_blogs, palette='mako', dodge=False)
    plt.title(f'入度最高的 Top {top_n} 博文 (被引用最多)')
    plt.xlabel('入度 (被引用次数)')
    plt.ylabel('博文标题')
    plt.yticks(fontsize=9)
    plt.tight_layout()
    plt.savefig(output_dir / "top_in_degree_blogs.png")
    # plt.show()
    print(f"图 12 (保存在 {output_dir / 'top_in_degree_blogs.png'}): 展示了入度最高的 {top_n} 篇博文。")
else:
    print("数据中没有足够的内部链接信息来生成 Top 入度博文图。")


# 3.6 Markdown 使用情况 (isMarkdown)
is_markdown_counts = df['isMarkdown'].value_counts()
if len(is_markdown_counts) > 1 : # 仅当有多个类别时才绘图
    plt.figure(figsize=(8, 6))
    is_markdown_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=sns.color_palette('Paired', 2))
    plt.title('Markdown 使用情况')
    plt.ylabel('') # Hide ylabel
    plt.legend(labels=['使用Markdown' if index else '未使用Markdown' for index in is_markdown_counts.index])
    plt.tight_layout()
    plt.savefig(output_dir / "markdown_usage_pie.png")
    # plt.show()
    print(f"图13 (保存在 {output_dir / 'markdown_usage_pie.png'}): 展示了使用Markdown编辑的博文比例。")
else:
    print("'isMarkdown' 列的值单一或数据不足，不生成Markdown使用情况饼图。")

print(f"\n所有分析和可视化图表生成完毕。图片已保存到 '{output_dir.resolve()}' 目录。")
print("请注意：部分图表（如标题相关的条形图）可能因标题过长而显示不全，实际使用中可能需要进一步调整字体大小或截断标题。")
print("对于分类ID (pCategoryLocation)，如果能提供ID与实际分类名称的对应关系，图表会更具可读性。")

