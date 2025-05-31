# generate_data_json.py

import pandas as pd
import ast
import json

def main():
    # 1. 读取 Excel
    df = pd.read_excel("../blog_list.xlsx", engine="openpyxl")

    # 2. 解析 counter 列，拆成四个数值列
    df['counter'] = df['counter'].apply(ast.literal_eval)
    counters = pd.json_normalize(df['counter'])
    # 根据实际列名调整
    df['readCount']    = counters['readCount'].astype(int)
    df['likeCount']    = counters['likeCount'].astype(int)
    df['commentCount'] = counters['commentCount'].astype(int)
    df['shareCount']   = counters['shareCount'].astype(int)

    # 3. 解析 id_links 列为 Python 列表，并全部转成整数
    def parse_links(x):
        if pd.isna(x) or x == "" :
            return []
        lst = ast.literal_eval(x)
        # 如果列表里是字符串 ID，则转成 int
        return [int(i) for i in lst]
    df['id_links'] = df['id_links'].apply(parse_links)

    # 4. 格式化时间为 ISO 字符串
    df['createTime'] = pd.to_datetime(df['createTime']) \
                         .dt.strftime("%Y-%m-%dT%H:%M:%S")

    # 5. 选取前端需要的字段并导出
    out = df[[
        'id',
        'title',
        'createTime',
        'readCount',
        'likeCount',
        'commentCount',
        'shareCount',
        'id_links'
    ]].to_dict(orient='records')

    # 6. 写入 JSON 文件
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("✅ data.json 已生成，共包含 %d 条记录。" % len(out))


if __name__ == "__main__":
    main()
