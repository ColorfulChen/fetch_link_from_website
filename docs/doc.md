# 网页链接爬虫系统改造方案

## 项目概述

将现有的爬虫脚本改造为支持定时调度、数据持久化、增量/全量策略的 Web 服务系统。

### 改造目标

1. ✅ 支持可配置的网站列表管理
2. ✅ 定时调度爬取任务（小时/天/月）
3. ✅ 增量和全量两种爬取策略
4. ✅ SQLite 数据库持久化存储
5. ✅ 爬取日志和指标记录（Valid Rate, Precision Rate）
6. ✅ 数据导出功能（增量/全量）
7. ✅ Flask REST API 接口
8. ⏳ Vue.js 前端界面（后期）

---

## 技术栈

### 后端
- **Python 3.8+**
- **Flask** - Web 框架
- **Flask-CORS** - 跨域支持
- **APScheduler** - 定时任务调度
- **PyMongo** - MongoDB 数据库驱动
- **MongoDB** - 远程 NoSQL 数据库
- **requests + BeautifulSoup** - 爬虫核心

### 前端（后期）
- Vue.js 3
- Element Plus
- Axios

---

## 数据库设计

### 1. websites 集合（网站配置）

```json
{
  "_id": ObjectId("..."),
  "name": "百度",
  "url": "https://www.baidu.com",
  "domain": "www.baidu.com",
  "status": "active",  // active/inactive
  "crawl_depth": 3,
  "max_links": 1000,
  "created_at": ISODate("2025-10-16T10:00:00Z"),
  "updated_at": ISODate("2025-10-16T10:00:00Z")
}
```

**索引：**
- `url`: unique
- `domain`: 1
- `status`: 1

### 2. crawl_tasks 集合（爬取任务记录）

```json
{
  "_id": ObjectId("..."),
  "website_id": ObjectId("..."),  // 引用 websites._id
  "task_type": "scheduled",  // scheduled/manual
  "strategy": "incremental",  // incremental/full
  "status": "completed",  // pending/running/completed/failed
  "started_at": ISODate("2025-10-16T10:00:00Z"),
  "completed_at": ISODate("2025-10-16T10:05:30Z"),
  "statistics": {
    "total_links": 850,
    "valid_links": 720,
    "invalid_links": 130,
    "new_links": 45,
    "valid_rate": 0.8471,
    "precision_rate": 0.9583
  },
  "error_message": null
}
```

**索引：**
- `website_id`: 1
- `status`: 1
- `started_at`: -1
- 复合索引: `{website_id: 1, started_at: -1}`

### 3. crawled_links 集合（爬取的链接）

```json
{
  "_id": ObjectId("..."),
  "website_id": ObjectId("..."),  // 引用 websites._id
  "task_id": ObjectId("..."),  // 引用 crawl_tasks._id
  "url": "https://www.baidu.com/page1",
  "domain": "www.baidu.com",
  "link_type": "valid",  // valid/invalid
  "status_code": 200,
  "content_type": "text/html",
  "first_crawled_at": ISODate("2025-10-16T10:00:00Z"),
  "last_crawled_at": ISODate("2025-10-16T10:00:00Z"),
  "crawl_count": 1,
  "source_url": "https://www.baidu.com"
}
```

**索引：**
- 复合唯一索引: `{website_id: 1, url: 1}` (unique)
- `domain`: 1
- `last_crawled_at`: -1
- `link_type`: 1

### 4. crawl_logs 集合（爬取日志）

```json
{
  "_id": ObjectId("..."),
  "task_id": ObjectId("..."),  // 引用 crawl_tasks._id
  "level": "INFO",  // INFO/WARNING/ERROR
  "message": "爬取任务已完成",
  "details": {
    "url": "https://example.com",
    "error": null
  },
  "created_at": ISODate("2025-10-16T10:00:00Z")
}
```

**索引：**
- `task_id`: 1
- `level`: 1
- `created_at`: -1
- 复合索引: `{task_id: 1, created_at: -1}`

### 5. schedules 集合（调度配置）

```json
{
  "_id": ObjectId("..."),
  "website_id": ObjectId("..."),  // 引用 websites._id
  "name": "百度每日爬取",
  "schedule_type": "daily",  // hourly/daily/monthly
  "cron_expression": "0 2 * * *",
  "strategy": "incremental",  // incremental/full
  "is_active": true,
  "next_run_time": ISODate("2025-10-17T02:00:00Z"),
  "last_run_time": ISODate("2025-10-16T02:00:00Z"),
  "created_at": ISODate("2025-10-16T10:00:00Z")
}
```

**索引：**
- `website_id`: 1
- `is_active`: 1
- `next_run_time`: 1

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     Vue.js Frontend                      │
│              (后期实现，本次暂不开发)                      │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────┴────────────────────────────────┐
│                    Flask Backend                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │            RESTful API Layer                     │   │
│  │  - 网站管理 API                                    │   │
│  │  - 任务管理 API                                    │   │
│  │  - 调度管理 API                                    │   │
│  │  - 数据导出 API                                    │   │
│  │  - 日志查询 API                                    │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Service Layer (业务逻辑层)              │   │
│  │  - CrawlerService (爬虫服务)                      │   │
│  │  - ScheduleService (调度服务)                     │   │
│  │  - ExportService (导出服务)                       │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │        Data Access Layer (数据访问层)             │   │
│  │  - PyMongo Database Client                       │   │
│  │  - Document Models & Validation                  │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         ↓
┌────────────────────────┴────────────────────────────────┐
│              APScheduler (定时任务调度器)                │
│  - 小时级调度 (CronTrigger)                             │
│  - 天级调度 (CronTrigger)                               │
│  - 月级调度 (CronTrigger)                               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│            远程 MongoDB 数据库 (NoSQL)                   │
│  Collections:                                           │
│  - websites, crawl_tasks, crawled_links                 │
│  - crawl_logs, schedules                                │
└─────────────────────────────────────────────────────────┘
```

---

## 核心功能模块设计

### 1. 爬虫核心模块 (CrawlerService)

#### 增量策略 (Incremental)

```python
def incremental_crawl(website_id, url, depth=3):
    """
    增量爬取策略：
    1. 查询数据库已爬取的链接
    2. 遇到已存在的链接时：
       - 更新 last_crawled_at
       - 增加 crawl_count
       - 不继续递归爬取其子链接
    3. 遇到新链接时：
       - 插入数据库
       - 继续递归爬取
    """
```

**优点**：
- 节省时间和资源
- 避免重复爬取
- 适合定期更新检查

**适用场景**：
- 日常定时爬取
- 内容更新检测

#### 全量策略 (Full)

```python
def full_crawl(website_id, url, depth=3):
    """
    全量爬取策略：
    1. 忽略数据库历史记录
    2. 爬取所有链接（去重仅在当前任务内）
    3. 所有链接都递归爬取
    4. 更新数据库中已存在的链接
    """
```

**优点**：
- 获取最新完整数据
- 发现链接结构变化
- 更新所有链接状态

**适用场景**：
- 首次爬取
- 网站结构大改
- 数据校验

### 2. 定时调度模块 (ScheduleService)

使用 **APScheduler** 实现：

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

# 小时级调度示例
scheduler.add_job(
    func=crawl_job,
    trigger=CronTrigger(minute=0),  # 每小时整点
    args=[website_id, 'incremental'],
    id=f'hourly_{website_id}'
)

# 天级调度示例
scheduler.add_job(
    func=crawl_job,
    trigger=CronTrigger(hour=2, minute=0),  # 每天凌晨2点
    args=[website_id, 'incremental'],
    id=f'daily_{website_id}'
)

# 月级调度示例
scheduler.add_job(
    func=crawl_job,
    trigger=CronTrigger(day=1, hour=0, minute=0),  # 每月1号零点
    args=[website_id, 'full'],
    id=f'monthly_{website_id}'
)
```

### 3. 数据导出模块 (ExportService)

#### 增量导出

```python
from bson import ObjectId

def export_incremental(website_id, since_date=None):
    """
    导出增量数据：
    - 导出指定日期之后新增的链接
    - 如果不指定日期，导出上次导出之后的新链接
    """
    query = {
        'website_id': ObjectId(website_id),
        'first_crawled_at': {'$gt': since_date}
    }
    links = db.crawled_links.find(query)
    return list(links)
```

#### 全量导出

```python
def export_full(website_id):
    """
    导出全量数据：
    - 导出该网站的所有历史链接
    """
    query = {'website_id': ObjectId(website_id)}
    links = db.crawled_links.find(query)
    return list(links)
```

**导出格式支持**：
- CSV
- JSON
- Excel (xlsx)

### 4. 日志监控模块

#### 爬取指标计算

```python
# Valid Rate (有效率)
valid_rate = valid_links / (valid_links + invalid_links)

# Precision Rate (精准率) - 可定义为成功下载的链接占比
precision_rate = successfully_downloaded / valid_links
```

#### 日志级别
- **INFO**: 任务启动、完成、常规操作
- **WARNING**: 链接访问失败、超时
- **ERROR**: 任务失败、系统错误

---

## REST API 设计

### 网站管理

#### 1. 添加网站

```http
POST /api/websites
Content-Type: application/json

{
  "name": "百度",
  "url": "https://www.baidu.com",
  "crawl_depth": 3,
  "max_links": 1000
}

Response: 201 Created
{
  "id": 1,
  "name": "百度",
  "url": "https://www.baidu.com",
  "domain": "www.baidu.com",
  "status": "active",
  "created_at": "2025-10-16T10:00:00"
}
```

#### 2. 获取网站列表

```http
GET /api/websites?status=active

Response: 200 OK
{
  "data": [
    {
      "id": 1,
      "name": "百度",
      "url": "https://www.baidu.com",
      "domain": "www.baidu.com",
      "status": "active",
      "last_crawl_time": "2025-10-16T09:00:00",
      "total_links": 1500
    }
  ],
  "total": 1
}
```

#### 3. 更新网站

```http
PUT /api/websites/{id}
{
  "name": "百度首页",
  "status": "inactive"
}

Response: 200 OK
```

#### 4. 删除网站

```http
DELETE /api/websites/{id}

Response: 204 No Content
```

### 任务管理

#### 5. 手动启动爬取任务

```http
POST /api/tasks/crawl
{
  "website_id": 1,
  "strategy": "incremental",  // 或 "full"
  "depth": 3,
  "max_links": 1000
}

Response: 202 Accepted
{
  "task_id": 123,
  "status": "pending",
  "message": "爬取任务已创建"
}
```

#### 6. 获取任务列表

```http
GET /api/tasks?website_id=1&status=completed&page=1&page_size=20

Response: 200 OK
{
  "data": [
    {
      "id": 123,
      "website_id": 1,
      "website_name": "百度",
      "strategy": "incremental",
      "status": "completed",
      "started_at": "2025-10-16T10:00:00",
      "completed_at": "2025-10-16T10:05:30",
      "total_links": 850,
      "valid_links": 720,
      "invalid_links": 130,
      "new_links": 45,
      "valid_rate": 0.8471,
      "precision_rate": 0.9583
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

#### 7. 获取任务详情

```http
GET /api/tasks/{task_id}

Response: 200 OK
{
  "id": 123,
  "website": {...},
  "strategy": "incremental",
  "status": "completed",
  "statistics": {
    "total_links": 850,
    "valid_links": 720,
    "invalid_links": 130,
    "new_links": 45,
    "valid_rate": 0.8471,
    "precision_rate": 0.9583,
    "duration_seconds": 330
  },
  "started_at": "2025-10-16T10:00:00",
  "completed_at": "2025-10-16T10:05:30"
}
```

#### 8. 停止任务

```http
POST /api/tasks/{task_id}/stop

Response: 200 OK
{
  "message": "任务已停止"
}
```

### 调度管理

#### 9. 创建调度任务

```http
POST /api/schedules
{
  "website_id": 1,
  "name": "百度每日爬取",
  "schedule_type": "daily",  // hourly/daily/monthly
  "hour": 2,  // 小时（daily/monthly时需要）
  "minute": 0,
  "day": 1,  // 日期（monthly时需要）
  "strategy": "incremental"
}

Response: 201 Created
{
  "id": 10,
  "website_id": 1,
  "name": "百度每日爬取",
  "schedule_type": "daily",
  "cron_expression": "0 2 * * *",
  "strategy": "incremental",
  "is_active": true,
  "next_run_time": "2025-10-17T02:00:00"
}
```

#### 10. 获取调度列表

```http
GET /api/schedules?website_id=1

Response: 200 OK
{
  "data": [
    {
      "id": 10,
      "website_name": "百度",
      "name": "百度每日爬取",
      "schedule_type": "daily",
      "cron_expression": "0 2 * * *",
      "strategy": "incremental",
      "is_active": true,
      "next_run_time": "2025-10-17T02:00:00",
      "last_run_time": "2025-10-16T02:00:00"
    }
  ]
}
```

#### 11. 启用/禁用调度

```http
PATCH /api/schedules/{id}
{
  "is_active": false
}

Response: 200 OK
```

#### 12. 删除调度

```http
DELETE /api/schedules/{id}

Response: 204 No Content
```

### 数据导出

#### 13. 导出爬取数据

```http
POST /api/export
{
  "website_id": 1,
  "export_type": "incremental",  // 或 "full"
  "format": "csv",  // csv/json/excel
  "since_date": "2025-10-01",  // 增量导出时使用
  "filters": {
    "link_type": "valid",  // 可选: valid/invalid
    "domain": "www.baidu.com"  // 可选: 按域名过滤
  }
}

Response: 200 OK
{
  "download_url": "/api/downloads/export_1234567890.csv",
  "file_name": "baidu_incremental_20251016.csv",
  "total_records": 450,
  "file_size": "125KB"
}
```

#### 14. 下载文件

```http
GET /api/downloads/{filename}

Response: 200 OK
Content-Type: text/csv
Content-Disposition: attachment; filename="baidu_incremental_20251016.csv"

url,domain,crawled_at
https://www.baidu.com/page1,www.baidu.com,2025-10-16 10:00:00
...
```

### 日志查询

#### 15. 获取任务日志

```http
GET /api/tasks/{task_id}/logs?level=ERROR&page=1

Response: 200 OK
{
  "data": [
    {
      "id": 1001,
      "level": "ERROR",
      "message": "Failed to fetch URL: https://example.com/page",
      "details": {
        "error": "Connection timeout",
        "url": "https://example.com/page"
      },
      "created_at": "2025-10-16T10:02:15"
    }
  ],
  "total": 15
}
```

#### 16. 获取统计数据

```http
GET /api/statistics?website_id=1&date_from=2025-10-01&date_to=2025-10-16

Response: 200 OK
{
  "website": {
    "id": 1,
    "name": "百度"
  },
  "period": {
    "from": "2025-10-01",
    "to": "2025-10-16"
  },
  "summary": {
    "total_tasks": 16,
    "completed_tasks": 15,
    "failed_tasks": 1,
    "total_links_crawled": 12500,
    "new_links_found": 850,
    "avg_valid_rate": 0.8523,
    "avg_precision_rate": 0.9421
  },
  "daily_stats": [
    {
      "date": "2025-10-16",
      "tasks": 1,
      "links": 850,
      "new_links": 45,
      "valid_rate": 0.8471
    }
  ]
}
```

---

## 项目目录结构

```
fetch_link_from_website/
│
├── app/
│   ├── __init__.py              # Flask app 初始化
│   ├── config.py                # 配置文件
│   │
│   ├── models/                  # 数据模型
│   │   ├── __init__.py
│   │   ├── website.py
│   │   ├── crawl_task.py
│   │   ├── crawled_link.py
│   │   ├── crawl_log.py
│   │   └── schedule.py
│   │
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── crawler_service.py   # 爬虫核心逻辑
│   │   ├── schedule_service.py  # 调度服务
│   │   └── export_service.py    # 导出服务
│   │
│   ├── api/                     # API 路由
│   │   ├── __init__.py
│   │   ├── websites.py          # 网站管理 API
│   │   ├── tasks.py             # 任务管理 API
│   │   ├── schedules.py         # 调度管理 API
│   │   ├── export.py            # 导出 API
│   │   └── statistics.py        # 统计 API
│   │
│   ├── utils/                   # 工具函数
│   │   ├── __init__.py
│   │   ├── response.py          # 统一响应格式
│   │   ├── validators.py        # 数据验证
│   │   └── logger.py            # 日志工具
│   │
│   └── database.py              # 数据库连接管理
│
├── scheduler/
│   ├── __init__.py
│   └── tasks.py                 # 定时任务定义
│
├── exports/                     # 导出文件存储目录
│
├── logs/                        # 日志文件目录
│
├── tests/                       # 测试文件
│   ├── test_crawler.py
│   ├── test_api.py
│   └── test_export.py
│
├── main.py                      # 原爬虫脚本（保留）
├── main_database.py             # 原数据库版本（保留）
├── run.py                       # Flask 应用启动入口
├── requirements.txt             # Python 依赖
├── .env                         # 环境变量（包含 MongoDB 连接配置）
└── README.md                    # 项目文档
```

---

## 实施步骤

### 阶段一：数据库和基础架构 (1-2天)

- [ ] 配置 MongoDB 远程连接
- [ ] 创建集合索引和数据验证规则
- [ ] 实现 PyMongo 数据库客户端封装
- [ ] 搭建 Flask 基础框架
- [ ] 配置日志系统
- [ ] 设置统一响应格式

### 阶段二：爬虫核心改造 (2-3天)

- [ ] 重构 `get_all_links` 支持数据库操作
- [ ] 实现增量爬取策略
- [ ] 实现全量爬取策略
- [ ] 添加爬取指标计算
- [ ] 实现错误处理和日志记录

### 阶段三：API 开发 (3-4天)

- [ ] 网站管理 API (CRUD)
- [ ] 任务管理 API
- [ ] 调度管理 API
- [ ] 数据导出 API
- [ ] 统计查询 API
- [ ] API 文档（Swagger）

### 阶段四：定时调度系统 (2天)

- [ ] 集成 APScheduler
- [ ] 实现小时/天/月级调度
- [ ] 调度任务的启动/停止/更新
- [ ] 调度状态监控

### 阶段五：数据导出功能 (1-2天)

- [ ] CSV 导出
- [ ] JSON 导出
- [ ] Excel 导出
- [ ] 增量/全量导出逻辑
- [ ] 文件下载接口

### 阶段六：测试和优化 (2-3天)

- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 错误处理完善
- [ ] 文档完善

### 阶段七：前端开发 (后期，5-7天)

- [ ] Vue.js 项目搭建
- [ ] 网站管理页面
- [ ] 任务监控页面
- [ ] 调度配置页面
- [ ] 数据查看和导出页面
- [ ] 统计图表

---

## 技术难点和解决方案

### 1. 增量爬取的去重逻辑

**问题**: 如何高效判断链接是否已爬取？

**解决方案**:
- 在 `crawled_links` 集合的 `(website_id, url)` 上创建复合唯一索引
- 爬取前先批量查询该网站的所有已爬取 URL，加载到 Set 中
- 使用内存 Set 进行快速去重判断

```python
from bson import ObjectId

# 爬取开始时加载已爬取的链接
crawled_docs = db.crawled_links.find(
    {'website_id': ObjectId(website_id)},
    {'url': 1}
)
crawled_urls = {doc['url'] for doc in crawled_docs}

# 爬取时判断
if url in crawled_urls:
    # 增量策略：不继续递归
    db.crawled_links.update_one(
        {'website_id': ObjectId(website_id), 'url': url},
        {
            '$set': {'last_crawled_at': datetime.utcnow()},
            '$inc': {'crawl_count': 1}
        }
    )
    return
```

### 2. 定时任务的并发控制

**问题**: 多个定时任务同时触发，可能导致资源竞争

**解决方案**:
- 使用任务锁机制（数据库级别）
- 检查是否有相同网站的任务正在运行
- 使用队列（如 Celery）进行任务排队（可选，高级方案）

```python
def crawl_job(website_id, strategy):
    # 检查是否有正在运行的任务
    running_task = db.crawl_tasks.find_one({
        'website_id': ObjectId(website_id),
        'status': 'running'
    })

    if running_task:
        logger.warning(f"Website {website_id} already has a running task")
        return

    # 创建并执行任务
    task_doc = {
        'website_id': ObjectId(website_id),
        'strategy': strategy,
        'status': 'running',
        'started_at': datetime.utcnow()
    }
    task_id = db.crawl_tasks.insert_one(task_doc).inserted_id
    # ...
```

### 3. 大数据量导出的性能问题

**问题**: 数据量大时，导出可能占用大量内存

**解决方案**:
- 使用流式导出（分批读取）
- 使用 MongoDB 的游标批量获取数据
- 后台异步生成文件，完成后通知下载

```python
import csv

def export_to_csv_streaming(query, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['url', 'domain', 'crawled_at'])

        # 使用游标批量获取数据，避免一次加载所有数据
        cursor = db.crawled_links.find(query).batch_size(1000)
        for doc in cursor:
            writer.writerow([
                doc['url'],
                doc['domain'],
                doc['last_crawled_at']
            ])
```

### 4. 爬虫被反爬虫机制阻止

**问题**: 频繁请求导致 IP 被封或返回 403

**解决方案**:
- 添加请求间隔（time.sleep）
- 随机 User-Agent
- 使用代理池（可选）
- 尊重 robots.txt（可选）

```python
import time
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    # 更多 User-Agent
]

def safe_request(url):
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }
    time.sleep(random.uniform(0.5, 2))  # 随机延迟
    return requests.get(url, headers=headers, timeout=5)
```

---

## 配置文件示例

### .env

```bash
# Flask 配置
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# MongoDB 数据库配置
MONGODB_URI=mongodb://username:password@host:port/database_name
# 或者使用 MongoDB Atlas
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name?retryWrites=true&w=majority
MONGODB_DB_NAME=crawler_db

# 爬虫配置
DEFAULT_CRAWL_DEPTH=3
DEFAULT_MAX_LINKS=1000
REQUEST_TIMEOUT=5
REQUEST_DELAY=1

# 导出配置
EXPORT_DIR=exports
MAX_EXPORT_SIZE=10000

# 调度器配置
SCHEDULER_TIMEZONE=Asia/Shanghai

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs
```

### requirements.txt

```txt
Flask==3.0.0
Flask-CORS==4.0.0
pymongo==4.6.0
APScheduler==3.10.4
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
chardet==5.2.0
python-dotenv==1.0.0
pandas==2.1.3
openpyxl==3.1.2
flasgger==0.9.7.1
dnspython==2.4.2
```

---

## 性能指标

### 预期性能

- **单个网站爬取速度**: 50-100 链接/分钟
- **数据库写入**: 1000+ 记录/秒
- **API 响应时间**: < 200ms (查询接口)
- **导出速度**: 10000 条记录/秒 (CSV)
- **支持并发任务**: 5-10 个网站同时爬取

### 优化建议

1. **数据库优化**
   - 创建合适的索引（复合索引、唯一索引）
   - 使用 MongoDB 的分片（Sharding）处理大数据量
   - 定期监控数据库性能和慢查询
   - 考虑使用 MongoDB Atlas 托管服务
   - 使用连接池管理数据库连接

2. **爬虫优化**
   - 使用连接池
   - 实现多线程爬取（谨慎使用，注意反爬）
   - 缓存 DNS 查询结果
   - 批量插入数据以提高写入性能

3. **API 优化**
   - 实现分页
   - 添加缓存（Redis）
   - 使用 GZIP 压缩响应
   - 使用 MongoDB 的聚合管道优化复杂查询

---

## 安全考虑

1. **输入验证**: 所有 API 输入进行严格验证
2. **SQL 注入防护**: 使用 SQLAlchemy 的参数化查询
3. **XSS 防护**: 对输出进行 HTML 转义
4. **速率限制**: 对 API 添加速率限制（Flask-Limiter）
5. **认证授权**: 添加 JWT 或 Session 认证（后期）

---

## 监控和维护

### 日志监控

- 任务执行日志: `logs/tasks_YYYYMMDD.log`
- API 访问日志: `logs/api_YYYYMMDD.log`
- 错误日志: `logs/error_YYYYMMDD.log`

### 健康检查

```http
GET /api/health

Response:
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running",
  "active_tasks": 2,
  "timestamp": "2025-10-16T10:00:00"
}
```

### 数据清理

- 定期清理过期的导出文件（7天）
- 定期归档旧日志（30天）
- 可选：清理超过 N 个月的爬取记录

---

## 总结

本方案将原有的单机爬虫脚本改造为：
- ✅ 支持定时调度的后台服务
- ✅ 支持增量/全量两种爬取策略
- ✅ 完整的数据持久化和导出
- ✅ RESTful API 接口
- ✅ 详细的日志和监控
- ⏳ 可扩展的前端界面（后期）

**预计总开发时间**: 12-18 天（不含前端）

**技术风险**: 低
**实施难度**: 中等
