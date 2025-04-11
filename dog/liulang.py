import sqlite3
import os
import json
import datetime

# 连接到db/archive.db数据库
conn = sqlite3.connect('db/archive.db')
# 创建一个游标对象
cursor = conn.cursor()

# 修改表名
table_name = 'webpages'
# 定义json文件所在的目录
json_dir = 'db/json'

# 初始化域名列表
domains = []

date_str = datetime.datetime.now().strftime('%Y-%m-%d')
# 获取当前文件的上级目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
# 修改json_path引用位置
json_path = os.path.join(parent_dir, 'db', 'json', f'{date_str}.json')
try:
    with open(json_path, 'r+', encoding='utf-8') as file:
        data = json.load(file)
        for entry in data:
            hostname = entry.get('host_name')
            domains.append(hostname)
except json.JSONDecodeError:
        print(f"Error decoding JSON file")

# 打印域名列表
print(domains)

# 新增数据库操作逻辑
from urllib.parse import urlparse

# 获取所有记录的URL
cursor.execute(f"SELECT url FROM {table_name}")
records = cursor.fetchall()

# 遍历每条记录进行处理
for url_tuple in records:
    original_url = url_tuple[0]
    # 提取域名（去掉协议头）
    parsed = urlparse(original_url)
    domain = parsed.netloc  # 获取网络位置部分（包含端口）
    
    # 检查域名是否在列表中
    if domain not in domains:
        # 直接删除不符合条件的记录
        cursor.execute(f"DELETE FROM {table_name} WHERE url = ?", (original_url,))

# 提交事务
conn.commit()


# 关闭游标和连接
cursor.close()
conn.close()
