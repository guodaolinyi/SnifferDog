# SnifferDog
自动化爬虫每天检查网站是否被篡改

## 模块说明
| 文件名|花名|描述|
|----------------|-------|--------------|
| dog_patrol.py |巡逻犬 |每天自动抓取目标网站内容 |
| frisbee.py | 狗狗飞盘 | 通过sites.txt 中配置的网站列表生成任务网站列表 |

## 核心功能
| 功能模块       | 描述                                                                 |
|----------------|----------------------------------------------------------------------|
| 定时爬取       | 每日自动抓取目标网站内容，支持自定义时间间隔                         |
| 篡改检测       | 基于哈希校验和内容对比算法，精确识别页面改动                         |
| 告警通知       | 发现篡改即时推送邮件/钉钉通知，支持多接收人配置                      |
| 报告生成       | 自动生成篡改检测报告，包含页面快照对比和变更统计                     |
| 白名单机制     | 可配置忽略特定页面或DOM元素，避免误报                                |
