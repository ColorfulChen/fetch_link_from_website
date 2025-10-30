# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介

这是一个网页链接爬虫系统,将简单的爬虫脚本改造为支持定时调度、数据持久化、增量/全量策略的 Web 服务系统。

**技术栈**:
- 后端: Flask + MongoDB + APScheduler
- 前端: Vue 3 + Element Plus + TailwindCSS
- 爬虫: requests + BeautifulSoup

## 常用命令

### 后端开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Flask 应用(包含调度器)
python run.py

# 运行单个爬虫脚本(原始版本)
python main.py <website_url>

# 测试数据库连接
python test_db.py
```

### 前端开发

```bash
cd frontend

# 安装依赖(必须使用 pnpm)
pnpm install

# 开发模式
pnpm dev

# 构建生产版本
pnpm build

# 构建后预览
pnpm preview:build

# 代码检查和格式化
pnpm lint
pnpm lint:eslint
pnpm lint:prettier
pnpm lint:stylelint

# 类型检查
pnpm typecheck
```

### 环境配置

1. 复制环境变量模板: `cp .env.example .env`
2. 配置 MongoDB 连接字符串和数据库名称
3. 配置 Flask 运行参数(主机、端口、调试模式)

## 核心架构

### 后端架构 (Flask)

```
app/
├── __init__.py         # Flask 应用工厂,注册蓝图,配置路由
├── config.py           # 全局配置(爬虫深度、延迟等)
├── database.py         # MongoDB 连接管理和索引创建
├── global_vars.py      # 全局变量管理(停止标志等)
│
├── models/             # 数据模型层(文档结构定义)
│   ├── website.py      # 网站模型
│   ├── crawl_task.py   # 爬取任务模型
│   └── ...
│
├── services/           # 业务逻辑层
│   └── crawler_service.py  # 核心爬虫逻辑(增量/全量策略)
│
├── api/                # API 路由层(蓝图)
│   ├── websites.py     # 网站管理 CRUD
│   ├── tasks.py        # 任务管理和执行
│   ├── schedules.py    # 调度任务管理
│   ├── export_api.py   # 数据导出(CSV/JSON/Excel)
│   └── statistics.py   # 统计数据查询
│
└── utils/              # 工具函数
    ├── logger.py       # 日志配置
    └── response.py     # 统一响应格式
```

### 关键设计

1. **爬虫策略**:
   - **增量模式 (incremental)**: 爬取前从数据库加载已爬取 URL 集合,遇到已存在链接时停止递归,仅更新 `last_crawled_at` 和 `crawl_count`
   - **全量模式 (full)**: 忽略历史记录,重新爬取所有链接,更新数据库中已存在的链接

2. **数据库集合**:
   - `websites`: 网站配置 (url 唯一索引)
   - `crawl_tasks`: 爬取任务记录 (website_id + started_at 复合索引)
   - `crawled_links`: 爬取的链接 ((website_id, url) 复合唯一索引)
   - `crawl_logs`: 爬取日志 (task_id + created_at 复合索引)
   - `schedules`: 调度配置 (website_id + is_active 索引)

3. **定时调度**: 使用 APScheduler,在 `scheduler/tasks.py` 中定义任务,支持小时/天/月级调度。调度器在 `run.py` 中初始化并启动。

4. **并发控制**: 创建任务前检查是否有相同网站的任务正在运行(`status='running'`),避免资源竞争。

5. **前后端集成**: Flask 应用在 `app/__init__.py` 中配置了 Vue 应用服务路由,从 `web/` 目录提供编译后的前端文件,支持 Vue Router 历史模式。

### 前端架构 (Vue 3)

基于 pure-admin-thin 模板构建,采用 Vue 3 + TypeScript + Vite + Element Plus。

## API 接口

所有 API 接口都在 `/api` 路径下:

- `/api/health` - 健康检查
- `/api/websites` - 网站管理 CRUD
- `/api/tasks` - 任务管理(创建、查询、日志)
- `/api/tasks/crawl` - 手动启动爬取任务
- `/api/schedules` - 调度任务管理
- `/api/export` - 数据导出(增量/全量)
- `/api/statistics` - 统计数据查询

详细 API 文档见 `docs/api.md`

## 重要注意事项

1. **MongoDB 连接**: 项目使用远程 MongoDB 数据库,需要在 `.env` 中配置 `MONGODB_URI` 和 `MONGODB_DB_NAME`

2. **ID 格式**: 所有 ID 都是 MongoDB ObjectId(24位十六进制字符串),使用 `from bson import ObjectId` 进行转换

3. **时间格式**: 统一使用 UTC 时间和 ISO 8601 格式

4. **爬虫配置**: 在 `app/config.py` 中定义了默认的爬取深度、最大链接数、请求延迟等参数

5. **日志管理**: 使用 `app/utils/logger.py` 配置的日志系统,日志文件保存在 `logs/` 目录

6. **导出文件**: 导出的文件保存在 `exports/` 目录,不纳入版本控制

7. **前端构建**: 前端构建产物在 `frontend/dist/` 目录,需要复制到 `web/` 目录供 Flask 服务

8. **pnpm 依赖管理**: 前端项目强制使用 pnpm(在 package.json 中配置了 preinstall 钩子)

## 开发工作流

### 添加新的 API 端点

1. 在 `app/models/` 中定义数据模型(如需要)
2. 在 `app/services/` 中实现业务逻辑
3. 在 `app/api/` 中创建路由和处理函数
4. 在 `app/__init__.py` 中注册新的蓝图
5. 在 `docs/api.md` 中添加 API 文档

### 添加新的调度任务

1. 在 `scheduler/tasks.py` 中定义任务函数
2. 在数据库 `schedules` 集合中创建调度配置
3. APScheduler 会自动加载并执行任务

### 修改爬虫逻辑

主要爬虫逻辑在 `app/services/crawler_service.py` 中:
- `incremental_crawl()` - 增量爬取
- `full_crawl()` - 全量爬取
- `safe_soup()` - 安全的 HTML/XML 解析
- `get_all_links()` - 递归链接提取

## 数据库索引

系统启动时会自动创建所有必要的索引(在 `app/database.py` 的 `create_indexes()` 方法中定义),包括:
- 唯一索引: `websites.url`, `(crawled_links.website_id, crawled_links.url)`
- 普通索引: 各集合的 website_id, status, created_at 等
- 复合索引: (website_id, started_at), (task_id, created_at) 等
