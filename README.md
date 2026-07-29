# NewsPulse — AI 驱动的金融要闻聚合平台

> 自动抓取 12+ 信息源 → AI 智能筛选打分 → 聚合展示 + 推送 + Obsidian 归档

![License](https://img.shields.io/badge/license-MIT-blue) ![Status](https://img.shields.io/badge/status-ready-green) ![Cost](https://img.shields.io/badge/monthly_cost-~%C2%A51-orange)

---

## 📁 项目结构

```
news-aggregator/
├── index.html          # 聚合网页前端（可直接打开使用）
├── rss-sources.json    # RSS 源矩阵配置（12个信息源）
├── n8n-workflow.json   # n8n 自动化工作流（导入即用）
├── ai-screening-prompt.md  # AI 筛选 Prompt 完整版
├── README.md           # 本文件
└── data/
    └── news-data.json  # 管道生成的数据文件（自动）
```

## ✨ 功能特性

### 网页端 (index.html)
- 🎯 **六大分类**：宏观政策 / 券商动态 / 公司公告 / 市场异动 / 海外联动 / 市场情绪
- ⭐ **AI 重要性评级**：1-5星滑块筛选，只看你关心的级别
- 🔍 **全文搜索**：标题 + 摘要联合检索
- ⚡ **自选股高亮**：涉及关注标的的条目橙色边框标识
- 📋 **简报模式**：一键切换紧凑视图
- 🕐 **时间轴分组**：按小时排列，看清事件发酵顺序
- 🌙 **暗色模式**：跟随系统偏好
- 📱 **响应式设计**：手机/平板/桌面完美适配

### 数据管道 (n8n)
- 🔄 每30分钟自动同步全部信息源
- 🤖 AI 自动打分、分类、写摘要、打标签
- 🚫 黑名单预过滤（砍掉60%噪音广告）
- ♻️ 智能去重（保留最高星级的版本）
- 📤 ≥4星重大事件自动推送通知
- 📝 自动生成 Obsidian 每日要闻笔记

## 🚀 快速开始（5分钟部署）

### 第一步：部署网页

**方式 A — 直接打开（演示模式）**
```bash
# 双击 index.html 即可在浏览器中查看（内置示例数据）
open index.html
```

**方式 B — GitHub Pages（推荐）**
```bash
git clone your-repo-url
cd your-repo
cp -r news-aggregator/* .
git add . && git commit -m "Add NewsPulse aggregator"
git push
# Settings → Pages → Source: main branch → Save
# 几分钟后访问 https://youruser.github.io/repo-name/
```

**方式 C — Vercel（一键部署）**
1. 访问 [vercel.com/new](https://vercel.com/new)
2. 导入你的 GitHub 仓库
3. 点击 Deploy，30秒完成

### 第二步：部署 RSSHub（可选但推荐）

如果你没有公共 RSSHub 实例：

```bash
# Docker 一键部署
docker run -d --name rsshub \
  -p 1200:1200 \
  -v ./data:/app/data \
  --restart unless-stopped \
  diygod/rsshub

# 访问 http://localhost:1200 验证
```

将 `http://localhost:1200` 填入 n8n credentials 的 `rssHubBaseUrl`。

### 第三步：部署 n8n 工作流

1. 安装 n8n（Docker 或 npm）
2. 打开 n8n 界面 → Import from File → 选择 `n8n-workflow.json`
3. 配置凭证：
   - **OpenAI API Key**（用于 AI 打分节点）
   - **RSSHub Base URL**（你的 RSSHub 地址）
4. 设置 Schedule Trigger 为每 30 分钟执行一次
5. 测试运行 → 手动点击 Execute

### 第四步：接入真实数据到网页

网页默认使用内置示例数据。接入真实数据有两种方式：

**方式 A — 静态 JSON（最简单）**

修改 `index.html` 底部的 `NEWS_DATA` 数组，替换为管道生成的 `news-data.json` 内容。或者用一个小脚本定时拉取：

```javascript
// 在 index.html 的 script 开头添加
async function loadLiveData() {
  try {
    const res = await fetch('./data/news-data.json');
    NEWS_DATA = await res.json();
    render();
  } catch(e) {
    console.log('使用内置示例数据');
  }
}
loadLiveData();
```

**方式 B — API 动态加载（进阶）**

让 n8n 工作流额外输出一个 HTTP Webhook，网页通过 fetch 实时获取。

## 💰 成本估算

| 组件 | 月费 | 说明 |
|------|------|------|
| RSSHub | ¥0 | 自托管免费 |
| n8n | ¥0 | 自托管免费（Cloud 免费档 5000次/月够用）|
| OpenAI API | ~¥1/月 | GPT-4o-mini，每日~500条新闻 |
| GitHub Pages/Vercel | ¥0 | 免费 |
| **合计** | **~¥1/月** | 一杯奶茶钱 |

如需更省，可将模型换为 DeepSeek-V3（价格约为 GPT-4o-mini 的 1/10）。

## 🔧 自定义配置

### 修改自选股列表

编辑 `rss-sources.json` 中的 `selfStockList` 字段：

```json
"selfStockList": ["600999", "06099", "招商证券", "茅台", "宁德时代"]
```

### 新增信息源

在 `rss-sources.json` 的 `sources` 数组中添加一项：

```json
{
  "id": "your_source_id",
  "name": "显示名称",
  "category": "快讯/政策/公告/深度/海外/情绪",
  "rssUrl": "https://rsshub.app/xxx/yyy",
  "priority": 1,
  "enabled": true,
  "notes": "备注说明"
}
```

然后在 `n8n-workflow.json` 中新增对应的 RSS Feed Read 节点并连接到 Merge 节点。

### 调整 AI 评分标准

编辑 `ai-screening-prompt.md` 中的评分标准和分类体系，然后更新 n8n LLM 节点的 system prompt 文本。

### 配置推送通知

n8n 工作流的「≥4星？」分支支持多种推送方式：

- **Server酱**（微信推送）：添加 HTTP Request 节点调用 Server酱 API
- **Bark**（iOS推送）：添加 Bark webhook 节点
- **Telegram Bot**：添加 Telegram 节点
- **邮件**：添加 Email Send 节点

## 🏗 架构总览

```
┌─────────────────────────────────────────────┐
│              信息源层 (12+ RSS)               │
│  财联社 · 见闻 · 巨潮 · 证监会 · 央行 · 财新… │
└──────────────────┬──────────────────────────┘
                   │ RSSHub 统一路由
                   ▼
┌─────────────────────────────────────────────┐
│              n8n 数据管道                     │
│  定时触发 → 合并 → 预过滤 → AI打分 → 去重     │
│       ↓         ↓         ↓                 │
│   news.json  Obsidian   推送通知              │
└──────────────────┬──────────────────────────┘
                   │ JSON / Markdown
                   ▼
┌─────────────────────────────────────────────┐
│            展示层 (index.html)                │
│  分类筛选 · 星级门槛 · 搜索 · 时间轴 · 简报    │
│  GitHub Pages / Vercel / 本地直开             │
└─────────────────────────────────────────────┘
```

## 📋 信息源清单

| # | 名称 | 类别 | 优先级 | 备注 |
|---|------|------|--------|------|
| 1 | 财联社电报 | 快讯 | ★★★★★ | 盘中最快源 |
| 2 | 金十数据 | 快讯 | ★★★★☆ | 宏观数据 |
| 3 | 格隆汇实时 | 快讯 | ★★★☆☆ | 港股联动 |
| 4 | 中国人民银行 | 政策 | ★★★★★ | 货币政策一手 |
| 5 | 证监会 | 政策 | ★★★★★ | 监管政策 |
| 6 | 发改委 | 政策 | ★★★★☆ | 宏观产业 |
| 7 | 财政部 | 政策 | ★★★★☆ | 财政政策 |
| 8 | 巨潮资讯网 | 公告 | ★★★★★ | 公司公告原文 |
| 9 | 上交所披露 | 公告 | ★★★★★ | 公告 |
| 10 | 深交所披露 | 公告 | ★★★★★ | 公告 |
| 11 | 财新网 | 深度 | ★★★★★ | 权威深度 |
| 12 | 第一财经 | 深度 | ★★★★☆ | 分析报道 |
| 13 | 21财经 | 深度 | ★★★☆☆ | 南方系 |
| 14 | 界面新闻 | 深度 | ★★★☆☆ | 商业财经 |
| 15 | 华尔街见闻 | 海外 | ★★★★★ | 全球市场 |
| 16 | 路透中文 | 海外 | ★★★★☆ | 国际通讯社 |
| 17 | 雪球热帖 | 情绪 | ★★★☆☆ | 社区情绪 |
| 18 | 东方财富股吧 | 情绪 | ★★☆☆☆ | 散户情绪 |

## ⚠️ 注意事项

1. **RSSHub 公共实例有限速**，建议自部署避免被限流
2. **财新部分内容需付费**，免费 RSS 只能获取部分文章
3. **社区类源（雪球/股吧）噪音较多**，AI 会自动降低其星级
4. **API Key 安全**：不要将 OpenAI Key 提交到公开 Git 仓库，使用 n8n Credentials 管理
5. **数据延迟**：RSS 抓取到网页展示有 1-30 分钟延迟（取决于管道执行间隔）

## 📄 License

MIT License — 自由使用、修改、分发

## 🤝 贡献

欢迎提交 Issue 和 PR！常见改进方向：
- 更多信息源适配
- 更精准的 AI 评分策略
- 移动端 PWA 支持
- 历史数据回溯和趋势图表
