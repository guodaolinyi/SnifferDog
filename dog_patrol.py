import requests
import hashlib
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
import difflib


def send_wechat_notification(content):
    """
    使用Server酱发送微信通知

    Args:
        content (str): 要发送的通知内容
    """
    # Server酱的API URL
    api_url = "https://sc.ftqq.com/SCU1234567890abcdef1234567890abcdef1234567890.send"

    # 构建请求数据
    data = {
        "text": "网页内容变化通知",
        "desp": content
    }

    # 发送POST请求
    response = requests.post(api_url, data=data)

    # 检查请求是否成功
    if response.status_code == 200:
        print("微信通知发送成功")
    else:
        print(f"微信通知发送失败: {response.text}")

def create_database():
    """
    创建 SQLite 数据库并初始化网页内容表
    """
    conn = sqlite3.connect('webpage_archive.db')
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

def save_webpage_to_database(conn, webpage_data):
    """
    将网页数据保存到 SQLite 数据库
    
    Args:
        conn (sqlite3.Connection): 数据库连接
        webpage_data (dict): 网页数据字典
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
                datetime.now().isoformat(), 
                webpage_data['status_code'], 
                webpage_data['encoding']
            ))
            print(f"新网址 {webpage_data['url']} 的内容已保存到数据库")
        
        else:
            # URL 已存在，比较哈希值
            existing_hash, existing_content = existing_record
            
            if existing_hash != content_hash:
                # 哈希值不同，插入新记录
                cursor.execute('''
                INSERT INTO webpages 
                (url, content, content_hash, domain, fetched_at, status_code, encoding) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    webpage_data['url'], 
                    webpage_data['content'], 
                    content_hash, 
                    parsed_url.netloc, 
                    datetime.now().isoformat(), 
                    webpage_data['status_code'], 
                    webpage_data['encoding']
                ))
                print(f"网址 {webpage_data['url']} 的内容已变化，新增记录")
                
                # 调用内容对比函数
                compare_content(existing_content, webpage_data['content'])
            else:
                print(f"网址 {webpage_data['url']} 的内容未变化，跳过保存")
        
        conn.commit()
    
    except sqlite3.Error as e:
        print(f"数据库保存错误: {e}")
        conn.rollback()

def fetch_webpage_content(url):
    """
    获取指定网页的内容并返回
    
    Args:
        url (str): 要获取内容的网页地址
    
    Returns:
        dict: 包含网页内容和元数据的字典
    """
    try:
        # 发送GET请求
        response = requests.get(url, timeout=10)
        
        # 检查请求是否成功
        response.raise_for_status()
        
        # 构建返回的数据字典
        webpage_data = {
            "url": url,
            "content": response.text,
            "status_code": response.status_code,
            "encoding": response.encoding,
            "fetched_at": datetime.now().isoformat()
        }
        
        return webpage_data
    
    except requests.RequestException as e:
        print(f"获取网页内容时发生错误: {e}")
        return None

def main():
    urls = [
        # 新官网
        #"http://sxbdcd.com",      # 陕西博德畅达网络传媒有限责任公司
        #"http://gzbdct.com",      # 贵州博德畅通网络传媒有限公司
        #"http://gsbdct.com",      # 甘肃博德畅通网络传媒有限责任公司
        #"http://bjbdct.com",      # 宝鸡博德畅通网络技术有限责任公司
        #"http://xashibang.cn",    # 西安世邦网络技术有限公司
        #"http://zybdct.com",      # 遵义博德畅通网络技术有限责任公司
        
        # 旧官网
        #"http://gsbybuild.com",   # 甘肃博远思创网络传媒有限公司
        #"http://gzbdbuild.com",   # 贵州省博德网络传媒有限公司
        #"http://sxbdbuild.com",   # 陕西博德网络传媒有限责任公司
        #"http://bjbdbuild.com"    # 宝鸡博德思创网络传媒有限公司

        "http://sxjbd.com/"
    ]
    
    # 创建数据库连接
    conn = create_database()
    
    try:
        for url in urls:
            try:
                webpage_data = fetch_webpage_content(url)
                
                if webpage_data:
                    # 计算网页内容的哈希值
                    content_hash = hashlib.sha256(webpage_data['content'].encode()).hexdigest()
                    print(f"网址 {url} 的内容哈希值为: {content_hash}")
                  
                    save_webpage_to_database(conn, webpage_data)
            
            except Exception as url_error:
                print(f"处理 {url} 时发生错误：{url_error}")
                continue
    
    except sqlite3.Error as db_error:
        print(f"数据库操作发生错误：{db_error}")
    
    except Exception as e:
        print(f"发生未知错误：{e}")
    
    finally:
        # 确保数据库连接被关闭
        if conn:
            conn.close()

if __name__ == "__main__":
    main()