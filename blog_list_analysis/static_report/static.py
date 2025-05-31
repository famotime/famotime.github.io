import pandas as pd
import numpy as np
from plotnine import *
import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.font_manager as fm
from io import BytesIO
import base64
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 设置图表主题
theme_set(theme_minimal() +
          theme(
              text=element_text(family='SimHei'),
              plot_title=element_text(size=14, hjust=0.5),
              axis_title=element_text(size=12),
              axis_text=element_text(size=10),
              legend_title=element_text(size=12),
              legend_text=element_text(size=10)
          ))

try:
    # 1. 数据加载与预处理
    df = pd.read_excel(Path('../blog_list.xlsx'))
    # counter 字段转 dict
    df['counter'] = df['counter'].apply(eval)
    for k in ['readCount','likeCount','commentCount','shareCount']:
        df[k] = df['counter'].apply(lambda x: x.get(k,0))
    # 时间字段
    df['createTime'] = pd.to_datetime(df['createTime'])
    df['updateTime'] = pd.to_datetime(df['updateTime'])
    # 引用列表
    df['id_links'] = df['id_links'].apply(lambda x: eval(x) if isinstance(x,str) and x.startswith('[') else [])

    # 2. 发文趋势
    trend_year = (df.groupby(df['createTime'].dt.year)['id'].count()
                    .reset_index().rename(columns={'id':'post_count','createTime':'year'}))
    trend_month = (df.groupby(df['createTime'].dt.to_period('M'))['id'].count()
                    .reset_index().rename(columns={'id':'post_count','createTime':'month'}))

    p1 = (ggplot(trend_year, aes('year','post_count')) +
          geom_col(fill='#1f77b4', width=0.7) +
          labs(title='年度发文数量', x='年份', y='发文数') +
          theme(figure_size=(8, 6)))

    p2 = (ggplot(trend_month, aes('month','post_count')) +
          geom_col(fill='#2ca02c', width=0.7) +
          theme(axis_text_x = element_text(angle=45, hjust=1)) +
          labs(title='月度发文数量', x='月份', y='发文数') +
          theme(figure_size=(12, 6)))

    # 3. 指标排行
    def top10_plot(col, title, color):
        top10 = df.sort_values(col, ascending=False).head(10)
        return (ggplot(top10, aes('reorder(title, '+col+')', col)) +
                geom_col(fill=color, width=0.7) +
                coord_flip() +
                labs(title=title, x='文章标题', y=col) +
                theme(figure_size=(10, 8)))

    p3 = top10_plot('readCount','阅读量TOP10','#e377c2')
    p4 = top10_plot('likeCount','点赞数TOP10','#ff7f0e')
    p5 = top10_plot('commentCount','评论数TOP10','#17becf')
    p6 = top10_plot('shareCount','分享数TOP10','#d62728')

    # 4. 指标分布
    p7 = (ggplot(df, aes('readCount')) +
          geom_histogram(bins=30, fill='#1f77b4', alpha=0.7) +
          labs(title='阅读量分布', x='阅读量', y='文章数') +
          theme(figure_size=(10, 6)))

    # 5. 引用关系网络
    edges = []
    for idx, row in df.iterrows():
        for target in row['id_links']:
            edges.append((str(row['id']), str(target)))
    G = nx.DiGraph()
    G.add_edges_from(edges)

    # 计算中心度
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())
    df['in_degree'] = df['id'].astype(str).map(in_degree).fillna(0).astype(int)
    df['out_degree'] = df['id'].astype(str).map(out_degree).fillna(0).astype(int)

    # 网络图
    plt.figure(figsize=(12,10))
    pos = nx.spring_layout(G, k=0.15)
    nx.draw_networkx_nodes(G, pos, node_size=20, node_color='blue', alpha=0.6)
    nx.draw_networkx_edges(G, pos, arrows=True, alpha=0.2)
    plt.title('博客文章引用关系网络')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('network.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 6. 输出HTML报告
    def fig_to_base64(fig):
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_str

    with open('report.html','w',encoding='utf8') as f:
        f.write("""
        <html>
        <head>
            <meta charset="utf-8">
            <title>博客数据分析报告</title>
            <style>
                body { font-family: SimHei, sans-serif; margin: 20px; }
                h1, h2, h3 { color: #333; }
                img { max-width: 100%; height: auto; margin: 10px 0; }
                .section { margin: 20px 0; }
            </style>
        </head>
        <body>
        <h1>博客数据分析与可视化报告</h1>
        <div class="section">
            <h2>1. 发文趋势</h2>
            <p>年度和月度的发文量如下图所示，整体创作持续且近年有明显活跃迹象。</p>
        """)
        f.write(f'<img src="data:image/png;base64,{fig_to_base64(p1.draw())}" />')
        f.write(f'<img src="data:image/png;base64,{fig_to_base64(p2.draw())}" />')
        f.write("""
        <div class="section">
            <h2>2. 各项指标TOP10</h2>
            <p>下面分别是阅读量、点赞、评论、分享数TOP10文章：</p>
        """)
        f.write(f'<img src="data:image/png;base64,{fig_to_base64(p3.draw())}" />')
        f.write(f'<img src="data:image/png;base64,{fig_to_base64(p4.draw())}" />')
        f.write(f'<img src="data:image/png;base64,{fig_to_base64(p5.draw())}" />')
        f.write(f'<img src="data:image/png;base64,{fig_to_base64(p6.draw())}" />')
        f.write("""
        <div class="section">
            <h2>3. 阅读量分布</h2>
            <p>大部分文章阅读量集中在较低区间，但也有极少数爆款。</p>
        """)
        f.write(f'<img src="data:image/png;base64,{fig_to_base64(p7.draw())}" />')
        f.write("""
        <div class="section">
            <h2>4. 文章引用关系网络</h2>
            <p>下图展示了博客间的互链引用结构。部分核心文章成为知识枢纽。</p>
            <img src="network.png" width=800>
            <h3>引用最多的文章TOP5</h3>
            <ul>
        """)
        for idx, row in df.sort_values('in_degree',ascending=False).head(5).iterrows():
            f.write(f"<li>{row['title']}（被引用{row['in_degree']}次）</li>")
        f.write("</ul>")
        f.write("<h3>最爱引用他文的文章TOP5</h3><ul>")
        for idx, row in df.sort_values('out_degree',ascending=False).head(5).iterrows():
            f.write(f"<li>{row['title']}（引用他文{row['out_degree']}次）</li>")
        f.write("</ul></div></body></html>")

    logging.info("报告生成完成！")

except Exception as e:
    logging.error(f"发生错误: {str(e)}")
    raise
