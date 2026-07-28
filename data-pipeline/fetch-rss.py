#!/usr/bin/env python3
"""
NewsPulse RSS 数据抓取 + AI 筛选管道
用法: python3 fetch-rss.py [--output news-data.json] [--api-key YOUR_OPENAI_KEY]

功能:
1. 从 18 个 RSS 源抓取最新新闻
2. 预过滤噪音（黑名单关键词）
3. 调用 LLM 打分/分类/写摘要/打标签
4. 去重后输出标准 JSON
5. 可被 GitHub Actions 定时调用，也可本地运行

依赖: pip install requests feedparser openai (或 deepseek)
"""

import json
import hashlib
import re
import sys
import argparse
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
try:
    import feedparser
    import requests
except ImportError:
    print("请先安装依赖: pip install requests feedparser")
    sys.exit(1)

# ============================================================
# 配置区 — 根据需要修改
# ============================================================

# LLM API 配置（二选一）
OPENAI_API_KEY = ""      # 留空则跳过 AI 打分，使用规则引擎
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-4o-mini"

# DeepSeek 替代方案（更便宜，约 1/10 价格）
DEEPSEEK_API_KEY = ""
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

# RSSHub 公共实例（建议自部署）
RSSHUB_BASE = "https://rsshub.rssforever.com"

# 自定义关注关键词（用于标记高亮）
WATCH_KEYWORDS = []

# ============================================================
# RSS 源定义
# ============================================================

RSS_SOURCES = [
    {"id": "cls_telegraph", "name": "财联社电报", "cat": "快讯",
     "url": f"{RSSHUB_BASE}/cls/telegraph", "priority": 1},
    {"id": "wallstreetcn", "name": "华尔街见闻", "cat": "海外",
     "url": f"{RSSHUB_BASE}/wallstreetcn/live", "priority": 1},
    {"id": "csrc", "name": "证监会", "cat": "政策",
     "url": f"{RSSHUB_BASE}/csrc/news", "priority": 1},
    {"id": "jin10", "name": "金十数据", "cat": "快讯",
     "url": f"{RSSHUB_BASE}/jin10/flash", "priority": 2},
    {"id": "caixin", "name": "财新网", "cat": "深度",
     "url": f"{RSSHUB_BASE}/caixin/latest", "priority": 2},
    {"id": "yicai", "name": "第一财经", "cat": "深度",
     "url": f"{RSSHUB_BASE}/yicai/latest", "priority": 2},
    {"id": "21jingji", "name": "21财经", "cat": "深度",
     "url": f"{RSSHUB_BASE}/21jingji/latest", "priority": 3},
    {"id": "pbc", "name": "央行", "cat": "政策",
     "url": f"{RSSHUB_BASE}/gov/pbc/news", "priority": 1},
    {"id": "ndrc", "name": "发改委", "cat": "政策",
     "url": f"{RSSHUB_BASE}/ndrc/news", "priority": 2},
    {"id": "mof", "name": "财政部", "cat": "政策",
     "url": f"{RSSHUB_BASE}/mof/news", "priority": 2},
    {"id": "xueqiu_hot", "name": "雪球热帖", "cat": "情绪",
     "url": f"{RSSHUB_BASE}/xueqiu/hot", "priority": 3},
    {"id": "reuters_cn", "name": "路透中文", "cat": "海外",
     "url": f"{RSSHUB_BASE}/reuters/china", "priority": 2},
    {"id": "gelonghui", "name": "格隆汇", "cat": "快讯",
     "url": f"{RSSHUB_BASE}/gelonghui/live", "priority": 3},
    {"id": "jiemian", "name": "界面新闻", "cat": "深度",
     "url": f"{RSSHUB_BASE}/jiemian/news", "priority": 3},
]

# 黑名单关键词（预过滤广告和垃圾内容）
BLACKLIST = ["广告", "推广", "软文", "荐股", "加群", "开户送",
             "内部消息", "涨停推荐", "老师带单", "免费领取"]

# 分类映射
CAT_MAP = {
    "快讯": "市场异动", "政策": "宏观政策", "深度": "宏观政策",
    "海外": "海外联动", "情绪": "市场情绪",
}

# ============================================================
# 核心逻辑
# ============================================================

def is_noise(title: str) -> bool:
    """检查标题是否命中黑名单"""
    t = title.lower()
    return any(kw in t for kw in [k.lower() for k in BLACKLIST])


def parse_time(entry) -> str:
    """解析时间为 HH:MM 格式"""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            t = datetime(*entry.published_parsed[:6])
            return t.strftime("%H:%M")
        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            t = datetime(*entry.updated_parsed[:6])
            return t.strftime("%H:%M")
    except (ValueError, TypeError):
        pass
    return datetime.now(timezone(timedelta(hours=8))).strftime("%H:%M")


def fetch_rss(source: Dict) -> List[Dict]:
    """从单个 RSS 源抓取新闻"""
    items = []
    try:
        resp = requests.get(source["url"], timeout=15,
                           headers={"User-Agent": "NewsPulse/1.0"})
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        for entry in feed.entries[:20]:  # 每源最多20条
            title = getattr(entry, 'title', '').strip()
            if not title or len(title) < 10:
                continue
            if is_noise(title):
                continue
            summary = getattr(entry, 'summary', '')[:300]
            link = getattr(entry, 'link', '#')
            items.append({
                "title": title,
                "source": source["name"],
                "category": CAT_MAP.get(source["cat"], source["cat"]),
                "time": parse_time(entry),
                "summary": re.sub(r'<[^>]+>', '', summary)[:200],
                "url": link,
                "_source_id": source["id"],
                "_priority": source["priority"],
            })
        print(f"  ✓ {source['name']}: 抓取 {len(items)} 条")
    except Exception as e:
        print(f"  ✗ {source['name']}: {str(e)}")
    return items


def deduplicate(items: List[Dict]) -> List[Dict]:
    """去重：按标题相似度"""
    seen = {}
    result = []
    for item in items:
        key = re.sub(r'\s+', '', item["title"].lower())
        # 简单哈希去重
        h = hashlib.md5(key.encode()).hexdigest()[:12]
        if h not in seen:
            seen[h] = item
            result.append(item)
        else:
            # 保留优先级更高的
            existing = seen[h]
            if item.get("_priority", 99) < existing.get("_priority", 99):
                idx = result.index(existing)
                result[idx] = item
                seen[h] = item
    return result


def rule_based_score(item: Dict) -> Dict:
    """规则引擎评分（当没有 AI 时使用）"""
    title = item["title"]
    summary = item.get("summary", "")
    text = title + summary

    star = 2  # 默认分

    # 5星：最高级别政策
    high_patterns = ["央行.*降准", "降息", "国常会", "国务院",
                     "证监会.*重大", "政治局", "国务院常务"]
    if any(re.search(p, text) for p in high_patterns):
        star = 5

    # 4星：重要政策/公告
    major_patterns = ["征求意见", "新规", "风控指标", "年报", "分红",
                      "业绩快报", "净利润.*亿", "营收.*亿", "美联储"]
    if star < 4 and any(re.search(p, text) for p in major_patterns):
        star = 4

    # 3星：一般相关
    normal_patterns = ["券商", "证券", "成交额", "两融", "北向资金",
                       "板块.*涨", "资金流向", "市占率", "数字化转型"]
    if star < 3 and any(re.search(p, text) for p in normal_patterns):
        star = 3

    # 社区类降权
    if item["source"] in ["雪球社区", "东方财富股吧"]:
        star = min(star, 2)

    # 提取标签
    tags = []
    tag_keywords = {
        "降准": r"降准", "货币政策": r"货币政", "流动性": r"流动性",
        "监管政策": r"监管|征求意见|新规", "风控指标": r"风控",
        "分红": r"分红|派", "年报": r"年报|业绩", "成交额": r"成交额",
        "两融": r"两融", "北向资金": r"北向", "美联储": r"美联储",
        "美股": r"美股|道指|纳斯达克", "数字化转型": r"数字化",
        "财政政策": r"财政|稳增长", "资本市场": r"资本市场",
    }
    for tag, pattern in tag_keywords.items():
        if re.search(pattern, text):
            tags.append(tag)
    tags = tags[:4]

    # 一句话摘要
    ai_summary = text[:50] + ("..." if len(text) > 50 else "")

    # 关键词匹配
    watched = False
    if WATCH_KEYWORDS:
        t_lower = text.lower()
        watched = any(kw.lower() in t_lower for kw in WATCH_KEYWORDS)

    return {
        "id": hashlib.md5(item["title"].encode()).hexdigest()[:12],
        "title": item["title"],
        "source": item["source"],
        "category": item["category"],
        "stars": star,
        "time": item["time"],
        "summary": ai_summary,
        "tags": tags,
        "watched": watched,
        "url": item["url"],
    }


def call_llm_ai_score(item: Dict, api_key: str, base_url: str, model: str) -> Optional[Dict]:
    """调用 LLM 进行智能评分"""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        prompt = f"""分析以下金融新闻并输出JSON：

标题：{item['title']}
来源：{item['source']}
预分类：{item['category']}
摘要：{item.get('summary', '')[:200]}
时间：{item['time']}
{"关注关键词：" + ",".join(WATCH_KEYWORDS) if WATCH_KEYWORDS else ""}

输出严格JSON（不要其他文字）：
{{"star":1-5,"category":"宏观政策|券商动态|公司公告|市场异动|海外联动|市场情绪","title_cleaned":"清洗后标题","summary_ai":"一句话摘要≤50字口语化","tags":["标签1","标签2"],"is_self_stock":true/false}}"""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": "你是专业金融新闻分析师。只输出合法JSON。"},
                      {"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)

        return {
            "id": hashlib.md5(item["title"].encode()).hexdigest()[:12],
            "title": result.get("title_cleaned", item["title"]),
            "source": item["source"],
            "category": result.get("category", item["category"]),
            "stars": result.get("star", 2),
            "time": item["time"],
            "summary": result.get("summary_ai", item.get("summary", "")[:100]),
            "tags": result.get("tags", [])[:4],
            "watched": result.get("is_self_stock", False),
            "url": item["url"],
        }
    except Exception as e:
        print(f"    AI 评分失败: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="NewsPulse RSS 数据管道")
    parser.add_argument("--output", "-o", default="news-data.json",
                        help="输出 JSON 文件路径")
    parser.add_argument("--api-key", default="", help="OpenAI API Key")
    parser.add_argument("--use-deepseek", action="store_true",
                        help="使用 DeepSeek 替代 OpenAI（更便宜）")
    parser.add_argument("--deepseek-key", default="", help="DeepSeek API Key")
    parser.add_argument("--keywords", default="", help="关注关键词，逗号分隔")
    parser.add_argument("--no-ai", action="store_true",
                        help="不使用 AI，仅规则引擎评分")
    args = parser.parse_args()

    global WATCH_KEYWORDS
    if args.keywords:
        WATCH_KEYWORDS = [k.strip() for k in args.keywords.split(",") if k.strip()]

    print(f"\n{'='*50}")
    print(f"NewsPulse 数据管道 · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    # Step 1: 抓取所有 RSS 源
    print("📡 第一步：抓取 RSS 数据...")
    all_items = []
    for src in RSS_SOURCES:
        items = fetch_rss(src)
        all_items.extend(items)
    print(f"\n  共抓取 {len(all_items)} 条原始数据")

    # Step 2: 去重
    print("\n🔄 第二步：去重处理...")
    deduped = deduplicate(all_items)
    print(f"  去重后剩余 {len(deduped)} 条")

    # Step 3: AI 评分 / 规则引擎
    use_ai = not args.no_ai and bool(args.api_key or OPENAI_API_KEY or
                                    (args.use_deepseek and (args.deepseek_key or DEEPSEEK_API_KEY)))

    if use_ai:
        api_key = args.api_key or OPENAI_API_KEY
        base_url = OPENAI_BASE_URL
        model = OPENAI_MODEL
        if args.use_deepseek:
            api_key = args.deepseek_key or DEEPSEEK_API_KEY
            base_url = DEEPSEEK_BASE_URL
            model = DEEPSEEK_MODEL

        print(f"\n🤖 第三步：AI 评分中... (模型: {model})")
        results = []
        for i, item in enumerate(deduped):
            print(f"  [{i+1}/{len(deduped)}] {item['title'][:30]}...", end="")
            scored = call_llm_ai_score(item, api_key, base_url, model)
            if scored:
                results.append(scored)
                print(f" ★{scored['stars']}")
            else:
                # fallback 到规则引擎
                fb = rule_based_score(item)
                results.append(fb)
                print(f" ★{fb['stars']} (规则)")
    else:
        print("\n⚙️ 第三步：规则引擎评分（无 AI）")
        results = [rule_based_score(item) for item in deduped]
        for r in results:
            print(f"  ★{r['stars']} | {r['title'][:40]}")

    # Step 4: 排序（星级优先，时间次之）
    results.sort(key=lambda x: (-x["stars"], x["time"]))

    # Step 5: 输出
    output = {
        "version": "1.0",
        "fetched_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "total_count": len(results),
        "major_count": len([r for r in results if r["stars"] >= 4]),
        "watched_count": len([r for r in results if r["watched"]]),
        "sources_used": len(RSS_SOURCES),
        "news": results,
    }

    import os as _os; _os.makedirs(_os.path.dirname(args.output), exist_ok=True) if _os.path.dirname(args.output) else None
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！输出: {args.output}")
    print(f"   总计: {output['total_count']} 条 | ≥4★: {output['major_count']} 条 | "
          f"关键词命中: {output['watched_count']} 条")


if __name__ == "__main__":
    main()
