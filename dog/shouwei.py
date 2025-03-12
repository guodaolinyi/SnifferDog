import ssl
import socket
import datetime
import logging
import os
import json
import time  # 导入 time 模块

# 配置日志记录
date_str = datetime.datetime.now().strftime('%Y-%m-%d')
log_dir = os.path.join('log', 'shouwei')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, f'{date_str}.log')
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 新增函数用于测试443端口是否正常
def test_port_443(hostname):
    try:
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            return True
    except (socket.gaierror, ConnectionRefusedError, socket.timeout):
        return False

def main():
    # 获取当日日期
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    json_path = os.path.join('db', 'json', f'{date_str}.json')
    try:
        with open(json_path, 'r+', encoding='utf-8') as file:
            data = json.load(file)
            for entry in data:
                hostname = entry.get('host_name')
                if hostname is None:
                    continue
                context = ssl.create_default_context()
                # 调用函数测试443端口
                if not test_port_443(hostname):
                    entry['ssl_status'] = -1  # 端口连接失败，将 ssl_status 设为 -1
                    logging.info(f"443端口连接 {hostname} 失败")
                    continue
                # 增加 100 毫秒的延迟
                time.sleep(0.1)
                try:
                    with socket.create_connection((hostname, 443)) as sock:
                        with context.wrap_socket(sock, server_hostname=hostname) as sslsock:
                            cert = sslsock.getpeercert()
                    if cert is not None:
                        # 确保 expiry_date_str 是字符串类型
                        expiry_date_str = str(cert['notAfter'])
                        expiry_date_obj = datetime.datetime.strptime(expiry_date_str, '%b %d %H:%M:%S %Y %Z')
                        # 转化为年月日日期
                        formatted_date = expiry_date_obj.strftime('%Y-%m-%d')
                        entry['ssl_date'] = formatted_date
                        entry['ssl_status'] = 1  # 支持 SSL，将 ssl_status 设为 1
                        logging.info(f"证书过期日期: {formatted_date}")
                    else:
                        entry['ssl_status'] = -1  # 不支持 SSL，将 ssl_status 设为 -1
                        logging.info(f"无法获取 {hostname} 的证书信息")
                except (socket.gaierror, ConnectionRefusedError, ssl.SSLError) as e:
                    entry['ssl_status'] = -1
                    logging.error(f"连接 {hostname} 时发生错误: {e}")
                    continue
                except ConnectionResetError as e:
                    entry['ssl_status'] = -1
                    logging.error(f"连接 {hostname} 时被远程主机重置连接: {e}")
                    continue
            # 将更新后的数据写回文件
            file.seek(0)  # 将文件指针移动到文件开头
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.truncate()  # 截断文件，防止旧数据残留
    except FileNotFoundError:
        logging.error(f"未找到 JSON 文件: {json_path}")
    except json.JSONDecodeError:
        logging.error(f"JSON 文件解析错误: {json_path}")

if __name__ == '__main__':
    main()