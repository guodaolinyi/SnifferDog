import json

# 读取sites.txt文件并补全URL协议
with open('sites.txt', 'r', encoding='utf-8') as file:
    raw_urls = [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]
    
    # 自动补全URL协议
    urls = []
    for url in raw_urls:
        if not url.startswith(('http://', 'https://')):
            urls.append(f'http://{url}')  # 修改为默认使用HTTP协议
            print(f"自动补全协议头: {url} -> http://{url}")
        else:
            urls.append(url)

# 生成任务列表（更新字段结构）
tasks = [{
    "url": url,
    "home_status": 0,        # 首页可访问状态 0-未检测 1-正常 0-异常
    "home_black": 0,         # 首页篡改状态 0-未篡改 1-已篡改
    "ssl_status": 0,         # SSL支持状态 0-不支持 1-支持
    "ssl_date": ""           # SSL证书到期日期
} for url in urls]

# 将任务列表保存为sites.json
with open('sites.json', 'w', encoding='utf-8') as file:
    json.dump(tasks, file, ensure_ascii=False, indent=4)
