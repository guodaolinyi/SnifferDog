import requests
import hashlib
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
import difflib
import datetime
import logging
import json
import os
import time
import re

# 移除 send_wechat_notification 函数
# def send_wechat_notification(content):
#     """
#     使用Server酱发送微信通知

#     Args:
#         content (str): 要发送的通知内容
#     """
#     # Server酱的API URL
#     api_url = "https://sc.ftqq.com/SCU1234567890abcdef1234567890abcdef1234567890.send"

#     # 构建请求数据
#     data = {
#         "text": "网页内容变化通知",
#         "desp": content
#     }

#     # 发送POST请求
#     response = requests.post(api_url, data=data)

#     # 检查请求是否成功
#     if response.status_code == 200:
#         print("微信通知发送成功")
#     else:
#         print(f"微信通知发送失败: {response.text}")

def create_database():
    """
    创建 SQLite 数据库并初始化网页内容表
    """
    # 修改数据库连接位置
    conn = sqlite3.connect('db/archive.db')
    cursor = conn.cursor()
    
    # 创建表，包含更多字段以便后续分析
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS webpages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        content TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        domain TEXT NOT NULL,
        fetched_at DATETIME NOT NULL,
        status_code INTEGER NOT NULL,
        encoding TEXT
    )
    ''')
    
    conn.commit()
    return conn

def compare_content(old_content, new_content):
    """
    逐行比较两段内容，找出修改的地方
    
    Args:
        old_content (str): 原始内容
        new_content (str): 新内容
    """
    # 过滤掉 input name="csrf_test_name" 的值
    def filter_csrf(content):
        return re.sub(r'<input[^>]*name="csrf_test_name"[^>]*value="[^"]*"[^>]*>', '<input name="csrf_test_name">', content)

    old_content = filter_csrf(old_content)
    new_content = filter_csrf(new_content)

    # 将内容按行分割
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    # 使用 difflib 进行更精确的比较
    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))
    
    # 存储变化的行
    added_lines = []
    removed_lines = []
    modified_lines = []
    
    for line in diff:
        if line.startswith('+ '):
            added_lines.append(line[2:])
        elif line.startswith('- '):
            removed_lines.append(line[2:])
        elif line.startswith('? '):
            # 标记有细微变化的行
            modified_lines.append(line[2:])
    
    # 打印变化信息
    print("\n=== 内容变化详情 ===")
    
    if added_lines:
        print("新增行：")
        for line in added_lines:
            print(f"  + {line}")
    
    if removed_lines:
        print("删除行：")
        for line in removed_lines:
            print(f"  - {line}")
    
    if modified_lines:
        print("修改行：")
        for line in modified_lines:
            print(f"  * {line}")
    
    if not (added_lines or removed_lines or modified_lines):
        print("内容未发生实质性变化")
    
    print("=== 内容变化结束 ===\n")

def save_webpage_to_database(conn, webpage_data, entry):  # 新增 entry 参数
    """
    将网页数据保存到 SQLite 数据库

    Args:
        conn (sqlite3.Connection): 数据库连接
        webpage_data (dict): 网页数据字典
        entry (dict): JSON 文件中的当前条目
    """
    cursor = conn.cursor()
    
    try:
        # 计算内容哈希值
        content_hash = hashlib.sha256(webpage_data['content'].encode()).hexdigest()
        
        # 解析 URL 获取域名
        parsed_url = urlparse(webpage_data['url'])
        
        # 查询数据库中是否已存在相同 URL 的记录
        cursor.execute('SELECT content_hash, content FROM webpages WHERE url = ? ORDER BY fetched_at DESC LIMIT 1', (webpage_data['url'],))
        existing_record = cursor.fetchone()
        
        def filter_csrf(content):
            return re.sub(r'<input[^>]*name="csrf_test_name"[^>]*value="[^"]*"[^>]*>', '<input name="csrf_test_name">', content)

        if existing_record is None:
            # URL 不存在，直接插入新记录
            cursor.execute('''
            INSERT INTO webpages 
            (url, content, content_hash, domain, fetched_at, status_code, encoding) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                webpage_data['url'], 
                webpage_data['content'], 
                content_hash, 
                parsed_url.netloc, 
                datetime.datetime.now().isoformat(),
                webpage_data['status_code'], 
                webpage_data['encoding']
            ))
            print(f"新网址 {webpage_data['url']} 的内容已保存到数据库")
            entry['home_has_change'] = 1  # 设置 home_has_change 为 1
        
        else:
            # URL 已存在，比较哈希值
            existing_hash, existing_content = existing_record
            
            if existing_hash != content_hash:
                # 过滤掉 csrf_test_name 的值
                filtered_existing_content = filter_csrf(existing_content)
                filtered_new_content = filter_csrf(webpage_data['content'])
                
                # 比较过滤后的内容
                if filtered_existing_content == filtered_new_content:
                    print(f"网址 {webpage_data['url']} 的内容除了 csrf_test_name 值外未变化，跳过保存")
                else:
                    # 哈希值不同且过滤后内容不同，插入新记录
                    cursor.execute('''
                    INSERT INTO webpages 
                    (url, content, content_hash, domain, fetched_at, status_code, encoding) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        webpage_data['url'], 
                        webpage_data['content'], 
                        content_hash, 
                        parsed_url.netloc, 
                        datetime.datetime.now().isoformat(),
                        webpage_data['status_code'], 
                        webpage_data['encoding']
                    ))
                    print(f"网址 {webpage_data['url']} 的内容已变化，新增记录")
                    entry['home_has_change'] = 1  # 设置 home_has_change 为 1
                    
                    # 调用内容对比函数
                    compare_content(existing_content, webpage_data['content'])
            else:
                print(f"网址 {webpage_data['url']} 的内容未变化，跳过保存")
        
        conn.commit()
    
    except sqlite3.Error as e:
        print(f"数据库保存错误: {e}")
        conn.rollback()

def fetch_webpage_content(url):
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            # 发送GET请求，不传递额外的请求头
            response = requests.get(url, timeout=10)
            
            # 检查请求是否成功
            response.raise_for_status()
            
            # 构建返回的数据字典
            webpage_data = {
                "url": url,
                "content": response.text,
                "status_code": response.status_code,
                "encoding": response.encoding,
                "fetched_at": datetime.datetime.now().isoformat()
            }
            
            return webpage_data
        
        except requests.RequestException as e:
            print(f"获取网页内容时发生错误: {e}，重试第 {retries + 1} 次")
            retries += 1
    
    print(f"尝试 {max_retries} 次后仍无法获取网页内容")
    return None

def main():
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    json_path = os.path.join('db', 'json', f'{date_str}.json')
    try:
        with open(json_path, 'r+', encoding='utf-8') as file:
            data = json.load(file)
            for entry in data:
                hostname = entry.get('host_name')
                if hostname and not hostname.startswith(('http://', 'https://')):
                    url = 'http://' + hostname
                    # 创建数据库连接
                    conn = create_database()
                    try:
                        # 增加100毫秒的延迟
                        time.sleep(0.1)
                        try:
                            webpage_data = fetch_webpage_content(url)
                            if webpage_data:
                                # 计算网页内容的哈希值
                                content_hash = hashlib.sha256(webpage_data['content'].encode()).hexdigest()
                                print(f"网址 {url} 的内容哈希值为: {content_hash}")
                                save_webpage_to_database(conn, webpage_data, entry)  # 传递 entry 参数
                                entry['home_status'] = 1  # 访问成功状态设为1
                            else:
                                entry['home_status'] = -1  # 访问失败状态设为-1
                        except Exception as url_error:
                            print(f"处理 {url} 时发生错误：{url_error}")
                            entry['home_status'] = -1  # 发生错误状态设为-1
                            continue
                    except sqlite3.Error as db_error:
                        print(f"数据库操作发生错误：{db_error}")
                        entry['home_status'] = -1  # 数据库错误状态设为-1
                    
                    except Exception as e:
                        print(f"发生未知错误：{e}")
                        entry['home_status'] = -1  # 未知错误状态设为-1
                    
                    finally:
                        # 确保数据库连接被关闭
                        if conn:
                            conn.close()
            # 将更新后的数据写回文件
            file.seek(0)
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.truncate()
    except FileNotFoundError:
        logging.error(f"未找到 JSON 文件: {json_path}")
    except json.JSONDecodeError:
        logging.error(f"JSON 文件解析错误: {json_path}")

if __name__ == "__main__":
    main()