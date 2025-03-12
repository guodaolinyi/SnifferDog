import json

# 读取sites.txt文件并处理注释
with open('sites.txt', 'r', encoding='utf-8') as file:
    raw_urls = []
    in_comment_block = False  # 多行注释标记
    
    for line in file:
        line = line.strip()
        if not line:
            continue
        
        # 处理多行注释
        if in_comment_block:
            if '*/' in line:
                line = line.split('*/', 1)[1].strip()
                in_comment_block = False
            else:
                continue
        if '/*' in line:
            if '*/' in line:  # 单行内的完整注释
                line = line.split('/*', 1)[0].strip() + line.split('*/', 1)[1].strip()
            else:
                line = line.split('/*', 1)[0].strip()
                in_comment_block = True
        
        # 处理单行注释
        if '#' in line:
            line = line.split('#', 1)[0].strip()
        
        if line:
            raw_urls.append(line)

    # 自动补全URL协议
    # 提取域名部分
    urls = []
    # 在文件顶部添加导入
    from urllib.parse import urlparse
    for url in raw_urls:
        # 解析URL结构
        parsed = urlparse(url)
        # 优先获取网络位置，若不存在则取路径的第一部分
        domain = parsed.netloc if parsed.netloc else parsed.path.split('/')[0]
        urls.append(domain)
        print(f"已处理URL: {url} -> {domain}")

# 生成任务列表（更新字段结构）
tasks = [{
    "host_name": url,   # 修改字段名
    "home_status": 0,   # 首页可访问状态 0-未检测 1-正常 -1-异常
    "home_has_change": 0,    # 首页篡改状态 0-未篡改 1-已篡改
    "ssl_status": 0,    # SSL支持状态 0-不支持 1-支持 -1-异常
    "ssl_date": "",     # SSL证书到期日期
    "has_change": 0,    # 是否有变化 0-无变化 1-有变化
    "has_prohibited_word": 0 # 是否存在违禁词 0-不存在 1-存在
} for url in urls]

# 新增导入
import os
from datetime import datetime

# 创建存储目录
os.makedirs('db/json', exist_ok=True)

# 生成带日期的文件名
date_str = datetime.now().strftime('%Y-%m-%d')
output_path = f'db/json/{date_str}.json'

# 将任务列表保存为带日期的json文件
with open(output_path, 'w', encoding='utf-8') as file:
    file.truncate(0)  # 清空文件内容
    json.dump(tasks, file, ensure_ascii=False, indent=4)
