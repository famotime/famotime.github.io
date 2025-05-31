import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from pyvis.network import Network
import ast

# 1. 读取数据
@st.cache_data
def load_data():
    df = pd.read_excel("blog_list.xlsx", engine="openpyxl")
    # 解析 counter 和 id_links
    df['counter'] = df['counter'].apply(ast.literal_eval)
    df = pd.concat([df.drop(['counter'], axis=1),
                    df['counter'].apply(pd.Series)], axis=1)
    df['createTime'] = pd.to_datetime(df['createTime'])
    df['id_links'] = df['id_links'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
    return df

df = load_data()
st.title("博客列表交互式分析报告")

# 2. 时间趋势分析
st.header("1. 文章发布频次 & 指标趋势")
df['year_month'] = df['createTime'].dt.to_period('M').astype(str)
count_ts = df.groupby('year_month').size().reset_index(name='post_count')
fig1 = px.bar(count_ts, x='year_month', y='post_count',
              title="每月发文量", labels={'year_month': '年月', 'post_count': '发文数'})
st.plotly_chart(fig1, use_container_width=True)

# 随着时间的推移各指标累积趋势
metrics = ['readCount','likeCount','commentCount','shareCount']
ts = df.set_index('createTime')[metrics].resample('M').sum().cumsum().reset_index()
fig2 = go.Figure()
for m in metrics:
    fig2.add_trace(go.Scatter(x=ts['createTime'], y=ts[m],
                              mode='lines', name=m))
fig2.update_layout(title="各项指标累积趋势（按月）", xaxis_title="时间", yaxis_title="累计次数")
st.plotly_chart(fig2, use_container_width=True)


# 3. 分布 & 排名
st.header("2. 阅读/点赞/评论/分享 分布与Top10")
col1, col2 = st.columns(2)

with col1:
    fig3 = px.histogram(df, x='readCount', nbins=50, title="阅读量分布")
    st.plotly_chart(fig3, use_container_width=True)
    top_reads = df.nlargest(10, 'readCount')[['id','title','readCount']]
    st.write("★ 阅读量Top10", top_reads)

with col2:
    fig4 = px.histogram(df, x='likeCount', nbins=30, title="点赞数分布")
    st.plotly_chart(fig4, use_container_width=True)
    top_likes = df.nlargest(10, 'likeCount')[['id','title','likeCount']]
    st.write("★ 点赞数Top10", top_likes)

col3, col4 = st.columns(2)
with col3:
    fig5 = px.histogram(df, x='commentCount', nbins=20, title="评论数分布")
    st.plotly_chart(fig5, use_container_width=True)
    st.write("★ 评论数Top10", df.nlargest(10, 'commentCount')[['id','title','commentCount']])
with col4:
    fig6 = px.histogram(df, x='shareCount', nbins=20, title="分享数分布")
    st.plotly_chart(fig6, use_container_width=True)
    st.write("★ 分享数Top10", df.nlargest(10, 'shareCount')[['id','title','shareCount']])


# 4. 指标相关性
st.header("3. 指标相关性分析")
corr = df[metrics].corr()
fig7 = px.imshow(corr, text_auto=True, title="阅读/点赞/评论/分享 相关系数矩阵")
st.plotly_chart(fig7, use_container_width=True)


# 5. 引用关系网络
st.header("4. 博客引用关系网络")
# 构建有向图
G = nx.DiGraph()
for _, row in df[['id','title','id_links']].iterrows():
    src = str(row['id'])
    G.add_node(src, title=row['title'])
    for tgt in row['id_links']:
        G.add_node(str(tgt))
        G.add_edge(src, str(tgt))

# 计算节点度数作为大小
deg = dict(G.in_degree())
nx.set_node_attributes(G, deg, 'in_deg')

# 将 NetworkX 图导入 PyVis
net = Network(height="600px", width="100%", directed=True, notebook=False)
for n, d in G.nodes(data=True):
    net.add_node(n, label=n, title=d.get('title', ''), value=d.get('in_deg', 1))
for u, v in G.edges():
    net.add_edge(u, v)

# 导出为 HTML 并在 Streamlit 中展示
net.save_graph('network.html')
st.components.v1.html(open('network.html','r',encoding='utf-8').read(), height=650)


# 6. 网络度量 & 排名
st.subheader("网络度量 Top10")
in_deg = sorted(G.in_degree(), key=lambda x: x[1], reverse=True)[:10]
out_deg = sorted(G.out_degree(), key=lambda x: x[1], reverse=True)[:10]
pr = sorted(nx.pagerank(G).items(), key=lambda x: x[1], reverse=True)[:10]
st.write("▶ 入度最高 Top10:", in_deg)
st.write("▶ 出度最高 Top10:", out_deg)
st.write("▶ PageRank 最高 Top10:", pr)
