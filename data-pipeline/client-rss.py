#!/usr/bin/env python3
"""
NewsPulse 客户端 RSS 抓取脚本（纯前端方案）
用法: 在浏览器控制台运行，或作为 Service Worker 使用

当无法使用后端管道时，此脚本提供纯前端 RSS 抓取能力。
由于浏览器 CORS 限制，需要通过公共 CORS 代理或 RSSHub 实例访问。
"""

# 此文件供参考，实际逻辑已内嵌在 index.html 的 JavaScript 中
# 浏览器端通过 fetch() 调用 RSSHub 公共实例获取数据

RSS_SOURCES = [
    ("财联社电报", "https://rsshub.app/cls/telegraph"),
    ("华尔街见闻", "https://rsshub.app/wallstreetcn/live"),
    ("证监会", "https://rsshub.app/csrc/news"),
    ("金十数据", "https://rsshub.app/jin10/flash"),
    ("财新网", "https://rsshub.app/caixin/latest"),
    ("第一财经", "https://rsshub.app/yicai/latest"),
    ("21财经", "https://rsshub.app/21jingji/latest"),
    ("央行", "https://rsshub.app/gov/pbc/news"),
    ("发改委", "https://rsshub.app/ndrc/news"),
    ("财政部", "https://rsshub.app/mof/news"),
    ("雪球热帖", "https://rsshub.app/xueqiu/hot"),
    ("路透中文", "https://rsshub.app/reuters/china"),
    ("格隆汇", "https://rsshub.app/gelonghui/live"),
    ("界面新闻", "https://rsshub.app/jiemian/news"),
]

# 黑名单
BLACKLIST = ["广告","推广","软文","荐股","加群","开户送",
             "内部消息","涨停推荐","老师带单"]

def is_noise(title):
    t = title.lower()
    return any(k in t for k in [k.lower() for k in BLACKLIST])
